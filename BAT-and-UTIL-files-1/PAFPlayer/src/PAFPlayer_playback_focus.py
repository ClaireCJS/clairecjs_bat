"""Authenticated local audio-focus leases for independent preview players."""
import contextlib
import json
import os
from pathlib import Path
import secrets
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class PlaybackFocus:
    def __init__(self, root, paused, enqueue, *, preview=False, pause='web_pause', resume='web_play', trace=None, guarded=False):
        self.root = Path(root) / 'playback-peers'
        self.paused, self.enqueue = paused, enqueue
        self.preview, self.pause, self.resume = preview, pause, resume
        self.identity = secrets.token_hex(16)
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.leases = {}
        self.restore = False
        self.guarded = guarded
        self.pending_pause = False
        self.pending_resume = False
        self.resume_inflight = False
        self.peers = []
        self.claimed = False
        self.started_ns = time.monotonic_ns()
        self.starting = bool(preview)
        self.held_before_start = False
        self.trace = trace or (lambda *_args, **_kwargs: None)
        self.server = None
        self.stopping = threading.Event()

    @staticmethod
    def process_alive(pid):
        """Skip exited Windows PIDs before any slow refused TCP connection."""
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            return False
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel.OpenProcess(0x1000, False, pid)
            if not handle:
                return ctypes.get_last_error() != 87  # Access denied is unknown, not dead.
            try:
                code = wintypes.DWORD()
                return not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value == 259
            finally:
                kernel.CloseHandle(handle)
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def retire(self, path):
        """Archive stale registration files; never delete or replace them."""
        retired = self.root / 'retired'
        retired.mkdir(exist_ok=True)
        target = retired / path.name
        suffix = 0
        while target.exists():
            suffix += 1
            target = retired / (path.stem + ' (%d)' % suffix + path.suffix)
        try:
            path.rename(target)
        except FileNotFoundError:
            pass  # A graceful shutdown may have archived it concurrently.

    @staticmethod
    def request(peer, payload, timeout=10):
        req = urllib.request.Request('http://127.0.0.1:%d/focus' % peer['port'],
            data=json.dumps(payload).encode(), headers={'X-PAF-Focus': peer['token'], 'Content-Type': 'application/json'})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=timeout) as response:
            return json.loads(response.read(4096))

    def start(self):
        if self.server is not None:
            return
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass
            def do_POST(self):
                try:
                    self.connection.settimeout(10)
                    if self.path != '/focus' or self.headers.get('Origin') or not secrets.compare_digest(self.headers.get('X-PAF-Focus', ''), owner.token):
                        raise ValueError('Unauthorized focus request')
                    size = int(self.headers.get('Content-Length', '0'))
                    if not 0 < size <= 2048:
                        raise ValueError('Invalid focus request size')
                    data = json.loads(self.rfile.read(size))
                    result = owner.handle(data)
                    body = json.dumps(result).encode()
                    self.send_response(200)
                except Exception:
                    body = b'{"ok":false}'
                    self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                with contextlib.suppress(OSError):
                    self.wfile.write(body)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, name='paf-preview-focus', daemon=True).start()
        self.root.mkdir(parents=True, exist_ok=True)
        # Exclusive unique names avoid replacing existing registry files.
        self.descriptor = self.root / (self.identity + '.json')
        with self.descriptor.open('x', encoding='utf-8') as target:
            json.dump({'port': self.server.server_port, 'token': self.token, 'pid': os.getpid(), 'identity': self.identity, 'preview': self.preview, 'started_ns': self.started_ns}, target)
        threading.Thread(target=self.maintain, name='paf-preview-leases', daemon=True).start()

    def handle(self, data):
        if not isinstance(data, dict) or set(data) != {'owner', 'action'} or not isinstance(data['owner'], str) or not 1 <= len(data['owner']) <= 64:
            raise ValueError('Invalid focus request')
        key, action = data['owner'], data['action']
        with self.lock:
            if action == 'pause':
                if not self.leases:
                    self.restore = self.pending_resume or self.resume_inflight or not bool(self.paused[0])
                self.pending_resume = False
                self.resume_inflight = False
                self.trace('preview.focus.lease', paused_before=bool(self.paused[0]),
                           resume_owned=self.restore, leases=len(self.leases) + int(key not in self.leases))
                self.leases[key] = time.monotonic() + 12
                if self.starting:
                    # A newer preview can pause us before our decoder exists.
                    # Acknowledge the silent state instead of waiting on our own
                    # startup thread to consume a queued pause (mutual deadlock).
                    self.held_before_start = True
                    self.paused[0] = True
                elif not self.paused[0]:
                    if self.guarded:
                        self.pending_pause = True
                    else:
                        self.enqueue(self.pause)
            elif action == 'refresh':
                if key not in self.leases:
                    return {'ok': False}
                self.leases[key] = time.monotonic() + 12
            elif action == 'release':
                self.leases.pop(key, None)
                self.restore_if_free()
            else:
                raise ValueError('Invalid focus action')
        if action == 'pause':
            deadline = time.monotonic() + 8
            while not self.paused[0] and time.monotonic() < deadline and not self.stopping.is_set():
                time.sleep(.02)
            return {'ok': bool(self.paused[0])}
        return {'ok': True}

    def restore_if_free(self):
        if not self.leases and self.restore:
            self.restore = False
            if self.held_before_start:
                self.held_before_start = False
                self.paused[0] = False
            elif self.guarded:
                self.pending_resume = True
            else:
                self.enqueue(self.resume)
            self.trace('preview.focus.restore-pending', guarded=self.guarded,
                       paused=bool(self.paused[0]), pending_resume=self.pending_resume)

    def observe_action(self, action, paused, *, toggle='pause-toggle', stop='web-stop'):
        """An explicit user Pause/Stop revokes any preview-owned future resume."""
        if action in {self.pause, stop} or (action == toggle and not paused):
            with self.lock:
                self.restore = False
                self.pending_resume = False
                self.resume_inflight = False
                self.trace('preview.focus.manual-hold', paused=bool(paused), leases=len(self.leases))

    def pop_action(self):
        """Resolve preview transport on the audio owner thread against current leases."""
        with self.lock:
            if self.pending_pause:
                self.pending_pause = False
                if self.leases and not self.paused[0]:
                    return self.pause
            if self.pending_resume:
                self.pending_resume = False
                if not self.leases and self.paused[0]:
                    self.resume_inflight = True
                    self.trace('preview.focus.restore-approved')
                    return self.resume
        return None

    def begin_resume(self):
        """Commit resume intent atomically so a newly arriving preview must pause it."""
        with self.lock:
            if self.leases:
                return False
            self.resume_inflight = False
            self.paused[0] = False
            return True

    def guard_action(self, action, paused, *, toggle='pause-toggle', external_resume='external-media-resume'):
        """A preview pause cannot be undone by stale Play or automatic media resume."""
        with self.lock:
            if self.leases and (action in {self.resume, external_resume} or (action == toggle and paused)):
                self.trace('preview.focus.resume-blocked', action=action, leases=len(self.leases))
                return None
        return action

    def claim(self):
        self.start()
        if not self.preview or self.claimed:
            return
        self.claimed = True
        started = time.monotonic()
        self.trace('preview.focus.start')
        try:
            for path in self.root.glob('*.json'):
                if path == self.descriptor:
                    continue
                try:
                    peer = json.loads(path.read_text(encoding='utf-8'))
                    if not isinstance(peer, dict) or not self.process_alive(peer.get('pid')):
                        self.trace('preview.focus.stale', peer_pid=peer.get('pid') if isinstance(peer, dict) else None)
                        self.retire(path)
                        continue
                    # The newest preview has priority. An older startup must not
                    # pause a newer preview that is already asking it to wait.
                    if peer.get('preview') and peer.get('started_ns', 0) > self.started_ns:
                        continue
                    self.trace('preview.focus.pause-request', peer_pid=peer.get('pid'))
                    # Remember before requesting: release even after a lost acknowledgement.
                    self.peers.append(peer)
                    result = self.request(peer, {'owner': self.identity, 'action': 'pause'})
                except TimeoutError as exc:
                    raise RuntimeError('Timed out waiting for another PAFPlayer to pause; preview has not started.') from exc
                except (OSError, ValueError, KeyError):
                    # Old descriptors are harmless: their random authentication token
                    # cannot control a different service that reuses the port.
                    continue
                if not result.get('ok'):
                    raise RuntimeError('Another PAFPlayer did not acknowledge pausing; preview has not started.')
                self.trace('preview.focus.paused', peer_pid=peer.get('pid'))
            while True:
                with self.lock:
                    waiting = bool(self.leases)
                    if not waiting:
                        self.starting = False
                        break
                if self.stopping.wait(.02):
                    raise InterruptedError('Preview startup was cancelled')
            self.trace('preview.focus.ready', elapsed_ms=round((time.monotonic() - started) * 1000, 2))
        except BaseException:
            self.release()
            self.claimed = False
            raise

    def release(self):
        with self.lock:
            peers, self.peers = self.peers, []
        for peer in peers:
            with contextlib.suppress(OSError, ValueError, KeyError):
                self.request(peer, {'owner': self.identity, 'action': 'release'}, timeout=.5)

    def maintain(self):
        while not self.stopping.wait(1):
            with self.lock:
                now = time.monotonic()
                self.leases = {key: expiry for key, expiry in self.leases.items() if expiry > now}
                self.restore_if_free()
                peers = list(self.peers)
            for peer in peers:
                with contextlib.suppress(OSError, ValueError, KeyError):
                    self.request(peer, {'owner': self.identity, 'action': 'refresh'}, timeout=.5)

    def close(self):
        self.stopping.set()
        self.release()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if hasattr(self, 'descriptor') and self.descriptor.exists():
            self.retire(self.descriptor)
