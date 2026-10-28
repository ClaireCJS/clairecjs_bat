"""Opt-in MonkeyMote/Winamp protocol adapter. See docs/monkeymote.md.

Wire format recovered from the locally installed, signed Winamp plug-in 2.5.0.
This is an interoperability experiment until verified with a real mobile client.
No listener, configuration writes, or ownership acquisition happen on import.
"""
from __future__ import annotations

import hashlib
import hmac
import io
import ipaddress
import json
from pathlib import Path, PureWindowsPath
import secrets
import socket
import struct
import threading
import time

MAGIC = 0x71D9873B
HEADER = struct.Struct('<III')
MAX_INPUT = 4096
MAX_TRACKS = 5000
HOME_NETWORKS = tuple(ipaddress.ip_network(x) for x in
                      ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))


def packet(kind, payload=b''):
    return HEADER.pack(MAGIC, kind, len(payload)) + payload


class Frames:
    """Bounded incremental TCP decoder; reject corrupt framing, never resync."""
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer.extend(data)
        result = []
        while len(self.buffer) >= HEADER.size:
            magic, kind, size = HEADER.unpack_from(self.buffer)
            if magic != MAGIC or size > MAX_INPUT:
                raise ValueError('Invalid MonkeyMote frame')
            end = HEADER.size + size
            if len(self.buffer) < end:
                break
            result.append((kind, bytes(self.buffer[HEADER.size:end])))
            del self.buffer[:end]
        if len(self.buffer) > MAX_INPUT + HEADER.size:
            raise ValueError('MonkeyMote input limit')
        return result


def text_bytes(value, limit=255):
    # Length fields count UTF-8 bytes; never split a multibyte character.
    text = str(value or '').replace('\0', ' ').replace('\r', ' ').replace('\n', ' ')
    return text.encode('utf-8')[:limit].decode('utf-8', 'ignore').encode('utf-8')


def milliseconds(value):
    try:
        return max(0, min(0xffffffff, int(float(value or 0) * 1000)))
    except (ValueError, TypeError, OverflowError):
        return 0


def track_hash(state):
    identity = state.get('track', {}).get('path') or json.dumps(state.get('metadata', {}), sort_keys=True)
    return hashlib.md5(str(identity).encode('utf-8'), usedforsecurity=False).digest()


def media_packet(kind, data, identity):
    # Native artwork (8) and lyrics (36) share size + track hash headers.
    return packet(kind, struct.pack('<I', len(data)) + identity + data +
                  (b'\0' if kind == 36 and data else b''))


def playback_order(queue):
    """Current visit, explicit requests, then the active order; never sort names."""
    entries = list(queue.get('entries') or [])
    current = queue.get('current')
    try:
        index = entries.index(current)
    except ValueError:
        index = -1
    if index >= 0:
        if queue.get('shuffled'):
            entries.pop(index)
        else:
            entries = entries[index + 1:] + entries[:index]
    queued = list(queue.get('next') or [])
    for path in queued:
        try:
            entries.remove(path)
        except ValueError:
            pass
    successor = queue.get('resume_successor')
    if not queued and successor in entries:
        entries.remove(successor)
        entries.insert(0, successor)
    return (([current] if current else []) + queued + entries)[:MAX_TRACKS]


def track_packet(state, index=0, current=True):
    meta = {str(k).casefold(): v for k, v in state.get('metadata', {}).items()}
    title = meta.get('song') or meta.get('title') or state.get('track', {}).get('filename', '')
    fields = [text_bytes(v) for v in (title, meta.get('artist'), meta.get('album'), meta.get('genre'))]
    body = bytearray(35)
    struct.pack_into('<II', body, 0, index & 0xffffffff, milliseconds(state.get('duration_seconds')))
    # Technical metadata/rating are deliberately absent. Bit 1 denotes current track.
    body[30] = 2 if current else 0
    body[31:35] = bytes(map(len, fields))
    body[14:30] = track_hash(state)
    return packet(5, bytes(body) + b''.join(x + b'\0' for x in fields))


def state_packet(state):
    volume = max(0, min(100, int(state.get('volume', 100))))
    level = round(volume * 65535 / 100)
    status = 3 if state.get('transport_stopped') or not state.get('playing') else 2 if state.get('paused') else 1
    return packet(6, struct.pack('<IBBBBH', milliseconds(state.get('position_seconds')),
                                 status, 0, 0, level // 257, level))


def playlist_packet(entries):
    rows = [struct.pack('<I', i) + text_bytes(label) + b'\0'
            for i, label in enumerate(entries[:MAX_TRACKS])]
    return packet(9, struct.pack('<I', len(rows)) + b''.join(rows))


def named_playlist_packet(entries, playlist_id, detailed=False):
    """Request 10: old opcode 31 or current opcode 50 (Winamp 10043670)."""
    entries = entries[:MAX_TRACKS]
    if not detailed:
        plain = playlist_packet(entries)[12:]
        return packet(31, plain[:4] + struct.pack('<I', playlist_id) + plain[4:])
    name = b'PAFPlayer'
    body = struct.pack('<IIHB', len(entries), playlist_id, len(name), 1) + name + b'\0'
    rows = []
    for index, label in enumerate(entries):
        title = text_bytes(label)
        row = bytearray(32)
        struct.pack_into('<I', row, 0, index)
        struct.pack_into('<H', row, 24, len(title))
        rows.append(bytes(row) + title + bytes(4))
    return packet(50, body + b''.join(rows))


def volume_percent(value):
    # Winamp plug-in accepts legacy low-byte volume and newer high-word volume.
    low, high = value & 0xffff, value >> 16
    level = (low & 255) * 257 if (not high and low & 255) or low & 0xff00 else high
    return round(level * 100 / 65535)


def validate_config(values):
    if not isinstance(values, dict) or not isinstance(values.get('enabled', False), bool):
        raise ValueError('MonkeyMote enabled must be true or false')
    if not values.get('enabled', False):
        return None
    address = ipaddress.IPv4Address(values.get('host', '127.0.0.1'))
    network = ipaddress.IPv4Network(values.get('trusted_subnet', '127.0.0.0/8'))
    loopback = address.is_loopback and network.subnet_of(ipaddress.ip_network('127.0.0.0/8'))
    home = any(address in n and network.subnet_of(n) for n in HOME_NETWORKS)
    if not (loopback or home) or address not in network:
        raise ValueError('MonkeyMote requires a specific loopback/home IPv4 address and matching trusted subnet')
    port = values.get('port', 19371)
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError('MonkeyMote port must be 1024..65535')
    password = values.get('password', '')
    if not isinstance(password, str) or len(password) > 128 or not password.isascii() or '\0' in password:
        raise ValueError('MonkeyMote password must be at most 128 ASCII characters')
    return dict(host=str(address), port=port, trusted_subnet=network, password=password.encode('ascii'))


def parse_options(arguments):
    """Consume only the opt-in JSON path; omission means disabled."""
    remaining, filename = [], None
    iterator = iter(arguments)
    for arg in iterator:
        if arg == '--monkeymote-config' or arg.startswith('--monkeymote-config='):
            if filename is not None:
                raise ValueError('Pass --monkeymote-config only once')
            filename = arg.partition('=')[2] if '=' in arg else next(iterator, '')
            if not filename:
                raise ValueError('--monkeymote-config requires a JSON file')
        else:
            remaining.append(arg)
    if filename is None:
        return remaining, None
    with Path(filename).open('rb') as stream:
        content = stream.read(8193)
    if len(content) > 8192:
        raise ValueError('MonkeyMote configuration exceeds 8 KiB')
    return remaining, validate_config(json.loads(content.decode('utf-8-sig')))


class PlayerAdapter:
    """Pinned to the original official instance; cannot acquire/promote ownership."""
    def __init__(self, app, runtime, server, *, explicit_instance=False):
        self.app, self.runtime, self.server = app, runtime, server
        self.instance = runtime.instance
        self.identity = self.instance.identity
        self.eligible = not explicit_instance and self.instance.owns()
        self._paths = ()
        self._playlist_cache = None
        self._playlist_at = 0.0
        self._pending = None
        self._art_key = None
        self._art_cache = b''

    def owns(self):
        return bool(self.eligible and self.runtime.instance is self.instance
                    and self.instance.identity == self.identity and self.instance.owns())

    def snapshot(self):
        if not self.owns():
            raise PermissionError('Official PAFPlayer ownership lost')
        # Copy only small fields, never artwork, lyric timelines or spectrum data.
        with self.server._lock:
            state = {k: self.server._state.get(k) for k in
                     ('playing', 'paused', 'transport_stopped', 'position_seconds',
                      'duration_seconds', 'volume', 'metadata', 'track')}
            state['_visit'] = getattr(self.server, '_art_worker_generation', 0)
        state['metadata'] = dict(state.get('metadata') or {})
        state['track'] = dict(state.get('track') or {})
        return state

    def playlist(self):
        if not self.owns():
            raise PermissionError('Official PAFPlayer ownership lost')
        if self._playlist_cache is not None and time.monotonic() - self._playlist_at < 1:
            return self._playlist_cache
        read = getattr(self.runtime, 'monkeymote_queue_read', None)
        queue = read() if read else {'entries': [], 'current': None}
        paths = playback_order(queue)
        if not paths:
            path = self.snapshot()['track'].get('path')
            paths = [path] if path else []
        path_token = tuple(paths)
        labels = (self._playlist_cache[0] if self._playlist_cache is not None and path_token == self._paths
                  else [PureWindowsPath(x).name for x in paths])
        try:
            current = paths.index(queue.get('current'))
        except ValueError:
            current = 0
        self._paths = path_token
        self._playlist_cache = (labels, current)
        self._playlist_at = time.monotonic()
        return self._playlist_cache

    def playlist_token(self):
        return self._paths

    def _transport_ready(self, state):
        if self._pending is None:
            return True
        kind, before, target, started = self._pending
        if time.monotonic() - started < .35 or not self.server._transport_actions.empty():
            return False
        if kind == 'pause':
            acknowledged = bool(state.get('paused')) == target
        else:
            acknowledged = (state.get('_visit'), state['track'].get('path')) != before
            acknowledged = acknowledged or not state.get('playing')
        if acknowledged:
            self._pending = None
        return acknowledged

    def play_selected(self, token, index):
        if not self.owns() or not token or not 0 <= index < len(token):
            return False
        state = self.snapshot()
        select = getattr(self.runtime, 'monkeymote_select', None)
        if select is None or not self._transport_ready(state):
            return False
        # Retain the displayed index's original path across queue rotations.
        # The session callback rechecks live membership under the playlist lock.
        if not self.owns() or not select(token[index]):
            return False
        self._pending = ('track', (state.get('_visit'), state['track'].get('path')), None, time.monotonic())
        self._playlist_at = 0
        return True

    def command(self, command, value=0):
        if not self.owns():
            return False
        if command == 6:
            return self.server.enqueue_action(f'{self.app.WEB_SET_PREFIX}volume:{volume_percent(value)}')
        if command not in (1, 2, 8, 9):
            return False
        state = self.snapshot()
        if not self._transport_ready(state):
            return False
        if command in (1, 2):
            paused = False if command == 1 else not bool(state.get('paused'))
            if command == 1 and state.get('playing') and not state.get('paused'):
                return True
            action = self.app.WEB_PAUSE if paused else self.app.WEB_PLAY
            pending = ('pause', None, paused, time.monotonic())
        else:
            action = self.app.NEXT_FILE if command == 8 else self.app.PREVIOUS_FILE
            pending = ('track', (state.get('_visit'), state['track'].get('path')), None, time.monotonic())
        if not self.server.enqueue_action(action):
            return False
        self._pending = pending
        return True

    def media(self, kind, index=0xffffffff):
        """Current cached media only; never scan the library or read phone paths."""
        if not self.owns():
            raise PermissionError('Official PAFPlayer ownership lost')
        _, current = self.playlist()
        with self.server._lock:
            identity = track_hash(self.server._state)
            if index not in (0xffffffff, current):
                return packet(13) if kind == 'art' else media_packet(36, b'', bytes(16))
            timeline = self.server._state.get('lyric_timeline') or []
            data = self.server._art_variants[0] if self.server._art_variants else None
            key = (identity, self.server._state.get('art_generation'))
        if kind == 'lyrics':
            lines = [str(row[1]) for row in timeline[:10000] if len(row) >= 2 and row[1]]
            raw = '\n'.join(lines).replace('\0', ' ').encode('utf-8')[:262144]
            raw = raw.decode('utf-8', 'ignore').encode('utf-8')
            return media_packet(36, raw, identity if raw else bytes(16))
        if not data:
            return packet(13)
        if self._art_key != key:
            from PIL import Image
            try:
                if len(data) > 32 * 1024 * 1024:
                    return packet(13)
                with Image.open(io.BytesIO(data)) as source:
                    if source.width * source.height > 32_000_000:
                        return packet(13)
                    source.thumbnail((1024, 1024))
                    output = io.BytesIO()
                    source.convert('RGB').save(output, format='JPEG', quality=85)
                    self._art_cache = output.getvalue()
            except (OSError, ValueError, Image.DecompressionBombError):
                return packet(13)
            self._art_key = key
        if not self.owns():
            raise PermissionError('Official PAFPlayer ownership lost')
        return media_packet(8, self._art_cache, identity)

    def media_revision(self):
        with self.server._lock:
            return (self.server._state.get('art_generation'),
                    self.server._state.get('lyric_timeline_revision'))


class Session:
    """Protocol state, separated from sockets for byte-level regression tests."""
    def __init__(self, adapter, password=b'', nonce=None, observe=None):
        self.adapter, self.password = adapter, password
        self.nonce = secrets.token_bytes(8) if nonce is None else nonce
        self.authenticated = False
        self.heartbeat = False
        self.suspended = False
        self.last_track = None
        self.playlist_token = None
        self.selected = None
        self.observed_playlist = None
        self.requested_media = set()
        self.last_media_revision = None
        self.observe = observe or (lambda event, **data: None)

    def greeting(self):
        return packet(1, struct.pack('<HB', 0x0302, bool(self.password)) + self.nonce)

    def updates(self, force=False):
        if not self.authenticated or self.suspended:
            return []
        state = self.adapter.snapshot()
        _, index = self.adapter.playlist()
        track = track_packet(state, index)
        result = []
        if force or track != self.last_track:
            result.append(track)
            result.append(packet(11, struct.pack('<I', index)))
            self.last_track = track
        token = self.adapter.playlist_token()
        if self.observed_playlist is not None and token != self.observed_playlist:
            result.append(packet(12))  # Native current-playlist invalidation.
        self.observed_playlist = token
        revision = (track_hash(state), self.adapter.media_revision())
        if revision != self.last_media_revision:
            for kind in sorted(self.requested_media):
                result.append(self.adapter.media(kind))
            self.last_media_revision = revision
        result.append(state_packet(state))
        return result

    def receive(self, kind, payload):
        if not self.adapter.owns():
            raise PermissionError('Official PAFPlayer ownership lost')
        # Log message numbers/sizes, never passwords, challenges or metadata.
        self.observe('receive', kind=kind, size=len(payload))
        self.suspended = kind == 16
        if not self.authenticated:
            if kind != 2 or len(payload) not in (16, 18):
                raise ValueError('MonkeyMote authentication required')
            expected = hashlib.md5(self.password + self.nonce, usedforsecurity=False).digest()
            self.authenticated = not self.password or hmac.compare_digest(payload[:16], expected)
            self.heartbeat = len(payload) == 18 and bool(payload[17])
            self.observe('authentication', accepted=self.authenticated)
            result = [packet(3, bytes([self.authenticated]))]
            if self.authenticated:
                if self.heartbeat:
                    result.append(packet(23))
                result += self.updates(True)
                result.append(packet(28, bytes(8)))  # No extended library capabilities advertised.
            return result
        if kind == 23 and not payload:  # Client heartbeat; no echo loop.
            return []
        if kind == 46 and not payload:
            return [packet(23)]
        if kind == 16:
            return []
        if kind == 22 and len(payload) == 16:  # Artwork hash acknowledgement.
            return []
        if kind == 7 and len(payload) == 5:
            command, value = struct.unpack('<BI', payload)
            if command == 10:
                self.selected = value
                accepted = self.playlist_token is not None and value < len(self.playlist_token)
            elif command == 1 and self.selected is not None:
                selected, self.selected = self.selected, None
                accepted = self.adapter.play_selected(self.playlist_token, selected)
            else:
                accepted = self.adapter.command(command, value)
            self.observe('command', command=payload[0], accepted=accepted)
            return []
        if kind == 4 and len(payload) in (5, 9):
            request, value = struct.unpack_from('<BI', payload)
            mode = struct.unpack_from('<I', payload, 5)[0] if len(payload) == 9 else 0
            self.observe('request', request=request, value=value, mode=mode)
            if request == 19:
                return [packet(51, bytes([0, 1, 1, 0]) + bytes(4))]
            if request == 10:
                labels, _ = self.adapter.playlist()
                if value == 0xffffffff:
                    self.playlist_token = self.adapter.playlist_token()
                    return [named_playlist_packet(labels, value, bool(mode))]
                return [packet(31, struct.pack('<II', 0, value))]
            if request == 13:
                return [packet(14, bytes(4))] if value == 0xffffffff else [packet(41, struct.pack('<III', 0, value, 0))]
            if request == 2:
                return [state_packet(self.adapter.snapshot())]
            if request == 4:
                labels, _ = self.adapter.playlist()
                self.playlist_token = self.adapter.playlist_token()
                return [playlist_packet(labels)]
            if request == 5:
                _, index = self.adapter.playlist()
                return [packet(11, struct.pack('<I', index))]
            if request == 1:
                _, index = self.adapter.playlist()
                if value in (0xffffffff, index):
                    return [track_packet(self.adapter.snapshot(), index, value == 0xffffffff)]
            if request in (3, 11):
                kind = 'art' if request == 3 else 'lyrics'
                if value == 0xffffffff or request == 11:
                    self.requested_media.add(kind)
                return [self.adapter.media(kind, value if request == 3 else 0xffffffff)]
            self.observe('unsupported_request', request=request)
            return []
        self.observe('unsupported_message', kind=kind, size=len(payload))
        return []


class Listener:
    """One bounded worker; slow/hostile clients never run on the audio thread."""
    def __init__(self, adapter, config, observe=None):
        self.adapter, self.config = adapter, config
        self.observe = observe or (lambda event, **data: None)
        self.stop_event = threading.Event()
        self.socket = self.client = self.thread = None

    def start(self):
        if not self.adapter.owns():
            raise PermissionError('MonkeyMote requires the original official PAFPlayer instance')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            sock.bind((self.config['host'], self.config['port']))
            sock.listen(1)
            sock.settimeout(.25)
        except BaseException:
            sock.close()
            raise
        self.socket = sock
        self.thread = threading.Thread(target=self.run, name='PAFPlayer MonkeyMote', daemon=True)
        try:
            self.thread.start()
        except BaseException:
            sock.close()
            raise
        return self

    def run(self):
        try:
            while not self.stop_event.is_set() and self.adapter.owns():
                try:
                    client, peer = self.socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                with client:
                    if ipaddress.ip_address(peer[0]) not in self.config['trusted_subnet']:
                        continue
                    self.client = client
                    try:
                        self.serve(client)
                    except (OSError, ValueError, PermissionError) as exc:
                        self.observe('disconnect', reason=type(exc).__name__)
                    except Exception as exc:
                        # Optional networking failure must not terminate playback.
                        self.observe('error', reason=type(exc).__name__)
                    finally:
                        self.client = None
        finally:
            if self.socket:
                self.socket.close()

    def serve(self, client):
        client.settimeout(.25)
        client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        session = Session(self.adapter, self.config['password'], observe=self.observe)
        client.sendall(session.greeting())
        decoder = Frames()
        started = last_data = last_update = last_heartbeat = window = time.monotonic()
        count = 0
        while not self.stop_event.is_set() and self.adapter.owns():
            now = time.monotonic()
            if now - last_data > 60 or (not session.authenticated and now - started > 5):
                break
            if now - window >= 1:
                window, count = now, 0
            try:
                data = client.recv(4096)
            except socket.timeout:
                data = None
            if data == b'':
                break
            if data:
                last_data = now
                frames = decoder.feed(data)
                count += len(frames)
                if count > 30:
                    raise ValueError('MonkeyMote request rate exceeded')
                for kind, payload in frames:
                    for response in session.receive(kind, payload):
                        client.sendall(response)
                    if kind == 2 and not session.authenticated:
                        return
            if now - last_update >= 1:
                for response in session.updates():
                    client.sendall(response)
                last_update = now
            if session.authenticated and session.heartbeat and now - last_heartbeat >= 2:
                client.sendall(packet(23))
                last_heartbeat = now

    def close(self):
        self.stop_event.set()
        for sock in (self.client, self.socket):
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                sock.close()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=.6)
