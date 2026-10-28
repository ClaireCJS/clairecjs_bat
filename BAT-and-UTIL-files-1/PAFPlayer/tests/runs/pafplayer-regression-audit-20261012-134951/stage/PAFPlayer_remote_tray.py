"""A Windows tray-only client and native tag viewer for another PAFPlayer host."""
from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import hashlib
import io
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, ProxyHandler
import webbrowser


def server_address(value):
    """Accept host:port (or an HTTP URL) without credentials or URL paths."""
    raw = str(value or '').strip()
    if not raw:
        raise ValueError('--tray-only requires a PAFPlayer hostname and port')
    parsed = urlsplit(raw if '://' in raw else 'http://' + raw)
    try:
        port = 666 if parsed.port is None else parsed.port
        host = parsed.hostname
    except ValueError as exc:
        raise ValueError('Invalid PAFPlayer server address') from exc
    if (parsed.scheme != 'http' or not host or parsed.username or parsed.password
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment
            or not 1 <= port <= 65535):
        raise ValueError('Use a plain HTTP hostname and port, such as machineservername:666')
    display_host = '[' + host + ']' if ':' in host else host
    return 'http://' + display_host + ':' + str(port) + '/', display_host + ':' + str(port)


class RemoteServer:
    """One fixed, verified HTTP target; no local playback or IPC ownership."""
    def __init__(self, address):
        self.url, self.label = server_address(address)
        self.enabled = True
        self._httpd = None
        self._opener = build_opener(ProxyHandler({}))
        self._lock = threading.RLock()
        self._state = {}
        self.connected = False
        self.owner_identity = ''
        self.last_error = 'Connecting…'
        self.stop_event = threading.Event()
        self._thread = None
        self.on_change = None
        self.poll_interval = 0.25
        self.clock_offset = 0.0

    def _read(self, path, *, timeout=3, limit=24 * 1024 * 1024):
        request = Request(self.url.rstrip('/') + path,
                          headers={'Accept': 'application/json', 'Cache-Control': 'no-store'})
        with self._opener.open(request, timeout=timeout) as response:
            data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError('PAFPlayer response exceeded the viewer limit')
            return data

    def json(self, path, *, timeout=3):
        return json.loads(self._read(path, timeout=timeout).decode('utf-8'))

    def image(self, generation, index):
        query = urlencode({'generation': generation, 'index': index})
        return self._read('/api/track-details/art?' + query, timeout=5, limit=20 * 1024 * 1024)

    def wallpaper(self, generation, width, height):
        if not self.connected or not self.owner_identity:
            return None
        if int(str(self.snapshot().get('version') or 'V0')[1:]) < 504:
            raise ValueError('Album-art wallpaper requires a V504 or newer player server')
        query = urlencode({'generation': generation, 'width': width, 'height': height,
                           'identity': self.owner_identity})
        return self._read('/api/track-details/wallpaper?' + query, timeout=7, limit=10 * 1024 * 1024)

    def snapshot(self):
        with self._lock:
            return dict(self._state)

    def _verify_status(self, value):
        if (not isinstance(value, dict) or str(value.get('program', '')).casefold() != 'pafplayer'
                or not re.fullmatch(r'V\d+', str(value.get('version', '')))):
            raise ValueError('The target did not identify itself as PAFPlayer')
        if int(str(value['version'])[1:]) < 503:
            raise ValueError('The target PAFPlayer must be V503 or newer for the tag viewer')
        return value

    def hello(self):
        sent = time.time()
        greeting = self._verify_status(self.json('/api/remote-tray/hello'))
        received = time.time()
        if isinstance(greeting.get('server_epoch'), (int, float)):
            self.clock_offset = float(greeting['server_epoch']) - (sent + received) / 2
        identity = greeting.get('identity')
        if not greeting.get('official') or not isinstance(identity, str) or not identity:
            raise ValueError('The target is not the official active PAFPlayer instance')
        state = self._verify_status(greeting.get('state'))
        if state['version'] != greeting['version']:
            raise ValueError('PAFPlayer changed owner during the status request')
        return identity, state

    def poll_once(self):
        try:
            identity, state = self.hello()
            with self._lock:
                changed = (not self.connected or self.owner_identity != identity
                           or self._state.get('version') != state.get('version'))
                self._state = state
                self.owner_identity = identity
                self.connected = True
                self.last_error = ''
        except Exception as exc:
            with self._lock:
                changed = self.connected or self.last_error != str(exc)
                self.connected = False
                self.owner_identity = ''
                self.last_error = str(exc)
        if changed and self.on_change:
            self.on_change()
        return self.connected

    def start_polling(self):
        if self._thread and self._thread.is_alive():
            return
        def run():
            while not self.stop_event.is_set():
                self.poll_once()
                self.stop_event.wait(self.poll_interval)
        self._thread = threading.Thread(target=run, name='paf-remote-tray-heartbeat', daemon=True)
        self._thread.start()

    def command(self, action, issued_at=None, expected_identity=None):
        if action not in ('previous', 'next', 'pause', 'stop', 'volume_up', 'volume_down',
                          'volume_mute', 'seek_forward', 'seek_back', 'seek_forward_fast',
                          'seek_back_fast', 'art_foreground', 'floating_foreground',
                          'floating_toggle'):
            raise ValueError('Unknown remote tray action')
        if (not self.connected or not self.owner_identity
                or (expected_identity is not None and expected_identity != self.owner_identity)):
            return False
        try:
            query = urlencode({'action': action, 'identity': self.owner_identity,
                               'client_epoch': '%.6f' % (time.time() if issued_at is None else issued_at)})
            answer = self.json('/api/remote-tray/action?' + query)
            return bool(answer.get('accepted'))
        except Exception:
            self.poll_once()
            return False

    def close(self):
        self.stop_event.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=3)


class RemoteHotkeys:
    """Edge-triggered transport keys and bounded auto-repeat volume controls."""
    VK = {'ctrl': 0x11, 'alt': 0x12, 'shift': 0x10, 'win_l': 0x5B,
          'win_r': 0x5C, 'c': 0x43, 'a': 0x41, 'f': 0x46,
          'up': 0x26, 'down': 0x28, 'media_prev': 0xB1,
          'media_next': 0xB0, 'media_pause': 0xB3, 'media_stop': 0xB2,
          'volume_up': 0xAF, 'volume_down': 0xAE, 'volume_mute': 0xAD}

    def __init__(self):
        self.held = set()
        self.repeat_at = {}

    def sample(self, down, now=None, epoch=None):
        now = time.monotonic() if now is None else now
        epoch = time.time() if epoch is None else epoch
        pressed = {name for name, code in self.VK.items() if down(code)}
        new = pressed - self.held
        self.held = pressed
        chord = 'ctrl' in pressed and 'alt' in pressed
        transport_modifier = 'ctrl' in pressed or 'alt' in pressed
        shift = 'shift' in pressed
        events = []
        def fire(target, action): events.append((target, action, epoch))
        if 'c' in new and ('win_l' in pressed or 'win_r' in pressed): fire('server', 'pause')
        if chord:
            if 'f' in new: fire('local' if shift else 'server', 'floating_toggle' if shift else 'floating_foreground')
            if 'a' in new: fire('local' if shift else 'server', 'art_toggle' if shift else 'art_foreground')
            for key, action in (('up', 'volume_up'), ('down', 'volume_down')):
                if key in pressed and now >= self.repeat_at.get(key, 0):
                    fire('server', action)
                    self.repeat_at[key] = now + (.32 if key in new else .085)
                if key not in pressed: self.repeat_at.pop(key, None)
        for key, action in (('media_pause', 'pause'), ('media_stop', 'stop'),
                            ('volume_mute', 'volume_mute')):
            if key in new: fire('server', action)
        if 'media_prev' in new: fire('server', 'previous' if transport_modifier else 'seek_back_fast' if shift else 'seek_back')
        if 'media_next' in new: fire('server', 'next' if transport_modifier else 'seek_forward_fast' if shift else 'seek_forward')
        for key, action in (('volume_up', 'volume_up'), ('volume_down', 'volume_down')):
            if key in pressed and now >= self.repeat_at.get(key, 0):
                fire('server', action)
                self.repeat_at[key] = now + (.32 if key in new else .085)
            if key not in pressed: self.repeat_at.pop(key, None)
        return events


def synchronized_position(state, local_epoch, clock_offset=0.0):
    """Advance the published audio clock using the server's measured wall clock."""
    try:
        position = float(state.get('lyric_position_seconds') or state.get('position_seconds') or 0)
        if state.get('playing') and not state.get('paused'):
            elapsed = max(0.0, min(4.0, local_epoch + clock_offset - float(state['lyric_clock_epoch'])))
            position += elapsed * float(state.get('speed') or 1)
        return max(0.0, position)
    except (KeyError, TypeError, ValueError):
        return 0.0


class RemoteTrayIdentity:
    """Owns only this client's icon, never the server's official mutex."""
    def owns(self):
        return True


def launch_viewer(address):
    """Give Tk its own main thread and process without creating another tray."""
    url, _label = server_address(address)
    app_module = sys.modules.get('PAFPlayer') or sys.modules['__main__']
    app_file = Path(app_module.__file__).resolve()
    executable = Path(sys.executable)
    flags = 0
    if os.name == 'nt' and executable.name.casefold() == 'python.exe':
        pythonw = executable.with_name('pythonw.exe')
        if pythonw.is_file():
            executable = pythonw
        else:
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    return subprocess.Popen([str(executable), str(app_file), '--tag-viewer', url],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, creationflags=flags)


def _remote_mutex(label):
    """One tray per target and Windows logon; kernel releases crashes safely."""
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.GetLastError.restype = wintypes.DWORD
    name = 'Local\\PAFPlayerRemoteTray-' + hashlib.sha256(label.casefold().encode('utf-8')).hexdigest()[:24]
    handle = kernel32.CreateMutexW(None, True, name)
    if not handle:
        raise OSError('Could not create the remote-tray mutex')
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return None
    return handle


def run_tray_only(arguments):
    if len(arguments) != 1:
        print('Usage: PAFPlayer --tray-only machineservername:666', file=sys.stderr)
        return 2
    if os.name != 'nt':
        print('The tray-only client requires Windows.', file=sys.stderr)
        return 2
    try:
        server = RemoteServer(arguments[0])
        mutex = _remote_mutex(server.label)
    except (ValueError, OSError) as exc:
        print('PAFPlayer: ' + str(exc), file=sys.stderr)
        return 2
    if mutex is None:
        print('PAFPlayer: a tray-only client for ' + server.label + ' is already running.')
        return 0
    from PAFPlayer_tray import TrayController
    stop = threading.Event()
    commands = queue.Queue(maxsize=64)
    hotkeys = RemoteHotkeys()
    def send_commands():
        while not stop.is_set():
            try: action, epoch, identity = commands.get(timeout=.2)
            except queue.Empty: continue
            server.command(action, epoch, identity)
    threading.Thread(target=send_commands, name='paf-remote-controls', daemon=True).start()

    class RemoteTrayController(TrayController):
        def poll_hotkeys(self):
            if not self._machine or not self._machine.options.get('remote_hotkeys', True): return
            user32 = ctypes.windll.user32
            for target, action, epoch in hotkeys.sample(lambda code: bool(user32.GetAsyncKeyState(code) & 0x8000)):
                if target == 'local':
                    self.dispatch('machine_remote_floating_lyrics' if action == 'floating_toggle' else 'machine_remote_album_art')
                else:
                    if server.connected:
                        try: commands.put_nowait((action, epoch, server.owner_identity))
                        except queue.Full: pass

        def tooltip_text(self):
            state = 'connected' if server.connected else 'disconnected'
            base = 'PAFPlayer remote · ' + server.label + ' · ' + state
            lyric = self._machine.tooltip_lyric() if self._machine else ''
            return base + (' · ' + lyric if lyric else '')

        def menu_items(self, state):
            active = server.connected
            label = 'Play' if state.get('paused') else 'Pause'
            return [(1, label, 'pause', active), (2, 'Previous track', 'previous', active),
                    (3, 'Next track', 'next', active), (4, 'Open web configuration', 'web', active),
                    (5, 'Open tag viewer', 'details', True),
                    (6, ('✓ ' if self._machine and self._machine.options['lyrics_tooltip'] else '○ ') + 'Live lyrics in tooltip', 'machine_lyrics_tooltip', True),
                    (7, ('✓ ' if self._machine and self._machine.options['album_wallpaper'] else '○ ') + 'Album art desktop wallpaper', 'machine_album_wallpaper', True),
                    (8, ('✓ ' if self._machine and self._machine.options.get('remote_hotkeys', True) else '○ ') + 'Capture control hotkeys here', 'machine_remote_hotkeys', True),
                    (9, ('✓ ' if self._machine and self._machine.options.get('remote_floating_lyrics') else '○ ') + 'Floating lyrics on this computer', 'machine_remote_floating_lyrics', True),
                    (10, ('✓ ' if self._machine and self._machine.options.get('remote_album_art') else '○ ') + 'Album art window on this computer', 'machine_remote_album_art', True),
                    (11, 'Server / version', 'about', True), (12, 'Exit this tray', 'exit', True)]

        def dispatch(self, action):
            if self._closing:
                return False
            if action.startswith('machine_') and self._machine:
                name = action.removeprefix('machine_')
                changed = self._machine.toggle(name)
                if changed and name in ('remote_floating_lyrics', 'remote_album_art') and self._machine.options.get(name):
                    overlays.start()
                return changed
            if action in ('previous', 'next', 'pause', 'stop', 'volume_up', 'volume_down',
                          'volume_mute', 'seek_forward', 'seek_back', 'seek_forward_fast',
                          'seek_back_fast', 'art_foreground', 'floating_foreground'):
                if not server.connected: return False
                try: commands.put_nowait((action, time.time(), server.owner_identity))
                except queue.Full: return False
                return True
            if action == 'details':
                launch_viewer(server.url)
                return True
            if action == 'web':
                webbrowser.open(server.url)
                return True
            if action == 'about':
                version = server.snapshot().get('version') or 'disconnected'
                message = 'PAFPlayer tray-only client\nServer: ' + server.label + '\nServer version: ' + str(version)
                if self._machine and self._machine.last_error:
                    message += '\nDesktop option: ' + self._machine.last_error
                self._message(message)
                return True
            if action == 'exit':
                stop.set()
                return True
            return False

    runtime = SimpleNamespace(server=server, app=SimpleNamespace(
        PROGRAM_VERSION='remote', load_player_settings=lambda: {}))
    tray = RemoteTrayController(runtime, RemoteTrayIdentity(), override=True)
    tray.attach_machine_options(remote=True)
    from PAFPlayer_remote_overlay import RemoteOverlays
    overlays = RemoteOverlays(server, tray._machine)
    if (tray._machine.options.get('remote_floating_lyrics')
            or tray._machine.options.get('remote_album_art')):
        overlays.start()
    server.on_change = tray.refresh
    server.start_polling()
    try:
        if not tray.start():
            print('PAFPlayer: could not create the remote tray icon.', file=sys.stderr)
            return 1
        while not stop.is_set() and tray._thread and tray._thread.is_alive():
            stop.wait(.25)
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        stop.set()
        overlays.close()
        tray.close()
        server.close()
        kernel32 = ctypes.windll.kernel32
        kernel32.ReleaseMutex(mutex)
        kernel32.CloseHandle(mutex)


def run_viewer(arguments):
    """Run a native Tk inspector; this mode never creates a tray or plays audio."""
    if len(arguments) != 1:
        print('Usage: PAFPlayer --tag-viewer machineservername:666', file=sys.stderr)
        return 2
    try:
        server = RemoteServer(arguments[0])
        import tkinter as tk
        from tkinter import ttk
    except (ValueError, ImportError) as exc:
        print('PAFPlayer tag viewer: ' + str(exc), file=sys.stderr)
        return 2
    root = tk.Tk()
    root.title('PAFPlayer tags · ' + server.label)
    root.geometry('980x700')
    root.minsize(650, 460)
    heading = ttk.Frame(root, padding=10)
    heading.pack(fill='x')
    title = ttk.Label(heading, text='Current track · ' + server.label, font=('Segoe UI', 14, 'bold'))
    title.pack(side='left')
    status = ttk.Label(root, text='Connecting to PAFPlayer…', padding=(10, 0))
    status.pack(fill='x')
    book = ttk.Notebook(root)
    book.pack(fill='both', expand=True, padx=10, pady=10)
    frames = {name: ttk.Frame(book) for name in ('Overview', 'Tags', 'Lyrics', 'Artwork', 'Technical')}
    for name, frame in frames.items():
        book.add(frame, text=name)

    def text_tab(frame):
        widget = tk.Text(frame, wrap='word', state='disabled', font=('Consolas', 10))
        bar = ttk.Scrollbar(frame, command=widget.yview)
        widget.configure(yscrollcommand=bar.set)
        widget.pack(side='left', fill='both', expand=True)
        bar.pack(side='right', fill='y')
        return widget

    overview = text_tab(frames['Overview'])
    lyrics = text_tab(frames['Lyrics'])
    artwork = text_tab(frames['Artwork'])
    technical = text_tab(frames['Technical'])
    columns = ('source', 'key', 'value')
    tags = ttk.Treeview(frames['Tags'], columns=columns, show='headings')
    for name, width in (('source', 90), ('key', 230), ('value', 550)):
        tags.heading(name, text=name.title())
        tags.column(name, width=width, stretch=True)
    tag_bar = ttk.Scrollbar(frames['Tags'], command=tags.yview)
    tags.configure(yscrollcommand=tag_bar.set)
    tags.pack(side='left', fill='both', expand=True)
    tag_bar.pack(side='right', fill='y')
    tag_detail = tk.Text(frames['Tags'], height=5, wrap='word', state='disabled')
    tag_detail.pack(side='bottom', fill='x')
    tag_rows = []
    def selected_tag(_event=None):
        selection = tags.selection()
        if not selection:
            return
        index = tags.index(selection[0])
        if index < len(tag_rows):
            fill(tag_detail, str(tag_rows[index][2]))
    tags.bind('<<TreeviewSelect>>', selected_tag)
    images = []
    current_identity = ['', -1]
    loading = [False]
    updates = queue.Queue()

    def fill(widget, value):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('end', value)
        widget.configure(state='disabled')

    def show(data, art_bytes):
        images.clear()
        file = data.get('file') or {}
        if not data.get('available'):
            status.configure(text=data.get('message') or 'No current track')
            for widget in (overview, lyrics, artwork, technical):
                fill(widget, 'No current track.')
            tags.delete(*tags.get_children())
            tag_rows.clear()
            fill(tag_detail, '')
            current_identity[:] = ['', int(data.get('art_generation') or 0)]
            return
        name = str(file.get('name') or 'Current track')
        status.configure(text=name + ' · ' + server.label)
        current_identity[:] = [str(file.get('path') or ''), int(data.get('art_generation') or 0)]
        facts = [('File', name), ('Path', file.get('path', '')),
                 ('Size', f"{int(file.get('size_bytes') or 0):,} bytes"),
                 ('Modified UTC', file.get('modified_utc', '')),
                 ('Duration', str(data.get('duration_seconds') or 'Unknown') + ' seconds')]
        fill(overview, '\n'.join(f'{key}: {value}' for key, value in facts))
        tags.delete(*tags.get_children())
        tag_rows.clear()
        for row in data.get('tags') or []:
            tag_rows.append(row)
            tags.insert('', 'end', values=tuple(str(value) for value in row[:3]))
        fill(tag_detail, '')
        cues = []
        for cue in data.get('lyrics') or []:
            start = float(cue.get('start') or 0)
            end = cue.get('end')
            marker = f'{start:.2f}s' + (f'–{float(end):.2f}s' if end is not None else '')
            cues.append(marker + '\n' + str(cue.get('text') or ''))
        fill(lyrics, (str(data.get('lyric_source') or '') + '\n\n' if cues else '') +
             ('\n\n'.join(cues) if cues else 'No lyrics were found.'))
        fill(technical, (str(data.get('technical_error') or '') + '\n\n' if data.get('technical_error') else '') +
             json.dumps(data.get('technical') or {}, ensure_ascii=False, indent=2))
        artwork.configure(state='normal')
        artwork.delete('1.0', 'end')
        for index, blob in enumerate(art_bytes):
            try:
                from PIL import Image, ImageTk
                with Image.open(io.BytesIO(blob)) as original:
                    image = original.copy()
                image.thumbnail((600, 450))
                photo = ImageTk.PhotoImage(image, master=root)
            except (ImportError, OSError, ValueError):
                try:
                    photo = tk.PhotoImage(data=base64.b64encode(blob).decode('ascii'), master=root)
                except tk.TclError:
                    artwork.insert('end', f'Image {index + 1} is unavailable (install Pillow for JPEG artwork).\n\n')
                    continue
            images.append(photo)
            artwork.insert('end', f'Image {index + 1} of {len(art_bytes)}\n')
            artwork.image_create('end', image=photo)
            artwork.insert('end', '\n\n')
        if not art_bytes:
            artwork.insert('end', 'No artwork is available for this track.')
        artwork.configure(state='disabled')

    def refresh():
        if loading[0]:
            return
        loading[0] = True
        status.configure(text='Reading ' + server.label + '…')
        def worker():
            try:
                server.hello()
                data = server.json('/api/track-details', timeout=12)
                art = []
                for index in range(max(0, int(data.get('art_count') or 0))):
                    try:
                        art.append(server.image(int(data['art_generation']), index))
                    except Exception:
                        pass
                updates.put(('details', data, art, None))
            except Exception as exc:
                updates.put(('details', None, [], str(exc)))
        threading.Thread(target=worker, name='paf-tag-viewer-load', daemon=True).start()

    def complete(data, art, error):
        loading[0] = False
        if error:
            status.configure(text='Could not reach ' + server.label + ': ' + error)
        else:
            show(data, art)

    def poll():
        def worker():
            try:
                _identity, state = server.hello()
                identity = [str((state.get('track') or {}).get('path') or ''),
                            int(state.get('art_generation') or 0)]
                if identity != current_identity:
                    updates.put(('refresh', None, None, None))
            except Exception:
                updates.put(('disconnected', None, None, None))
        threading.Thread(target=worker, name='paf-tag-viewer-poll', daemon=True).start()
        root.after(3000, poll)

    def drain_updates():
        try:
            while True:
                kind, data, art, error = updates.get_nowait()
                if kind == 'details':
                    complete(data, art, error)
                elif kind == 'refresh':
                    refresh()
                elif kind == 'disconnected':
                    status.configure(text='Disconnected from ' + server.label)
        except queue.Empty:
            pass
        root.after(100, drain_updates)

    ttk.Button(heading, text='Refresh', command=refresh).pack(side='right')
    refresh()
    root.after(3000, poll)
    root.after(100, drain_updates)
    root.mainloop()
    return 0
