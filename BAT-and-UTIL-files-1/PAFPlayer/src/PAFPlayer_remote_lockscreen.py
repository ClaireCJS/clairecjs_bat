"""Local lock-screen bridge and guided setup for the remote tray client."""
from __future__ import annotations
import json
import os
import queue
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


def status_payload(server, identity, remote_identity, show_version=False, now=None):
    """Publish only a currently verified remote session, with a local lease."""
    from PAFPlayer_remote_tray import synchronized_position
    from PAFPlayer_lockscreen import lockscreen_lyric_context
    with server._lock:
        if not server.connected or not server.owner_identity or server.owner_identity != remote_identity:
            return None
        state = dict(server._state)
        offset = server.clock_offset
    version = str(state.get('version') or '')
    if str(state.get('program', '')).casefold() != 'pafplayer' or not version:
        return None
    def limited(value): return str(value or '')[:2048]
    metadata = state.get('metadata') if isinstance(state.get('metadata'), dict) else {}
    track = state.get('track') if isinstance(state.get('track'), dict) else {}
    playing = bool(state.get('playing')); paused = bool(state.get('paused'))
    stopped = bool(state.get('transport_stopped'))
    position = synchronized_position(state, time.time() if now is None else now, offset)
    lyric, previous = lockscreen_lyric_context(
        state.get('lyric_timeline'), position, state.get('karaoke_offset_seconds', 0),
        limited(state.get('lyric')), playing=playing, paused=paused, stopped=stopped,
        speed=state.get('speed', 1.0))
    output = {'program':'PAFPlayer', 'version':version, 'playing':playing, 'paused':paused,
              'transport_stopped':stopped, 'position_seconds':position,
              'metadata':{key:limited(metadata.get(key)) for key in
                          ('Artist','artist','Song','title','Album','album','Year','year','Date','date')},
              'track':{'filename':limited(track.get('filename'))},
              'lyric':limited(lyric), 'lyric_previous':limited(previous),
              'lockscreen_show_version':bool(show_version)}
    duration = state.get('duration_seconds')
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        output['duration_seconds'] = duration
    return {'program':'PAFPlayer', 'version':version, 'official':True,
            'identity':identity, 'state':output}


def supported_version(found, required):
    try:
        return tuple(int(part) for part in str(found).split('.')) >= tuple(int(part) for part in str(required).split('.'))
    except (TypeError, ValueError):
        return False


def inspect_companion():
    """Inspect this Windows account and certificate store without installing."""
    from PAFPlayer_lockscreen import EMBEDDED_INSTALL_VERSION
    from PAFPlayer_lockscreen_installer import WindowsBackend, require_windows_10
    require_windows_10()
    backend = WindowsBackend()
    version = backend.installed_version()
    trusted = backend.trusted()
    uac = backend.uac_enabled() if not trusted else None
    return version, EMBEDDED_INSTALL_VERSION, trusted, uac


class RemoteLockScreen:
    """One local publisher; verify and set up the companion by default."""
    KEY = 'RemoteLockScreenEnabled'
    VERSION_KEY = 'RemoteLockScreenShowVersion'
    GUIDE_KEY = 'RemoteLockScreenGuideAcknowledged'
    def __init__(self, server, settings, launcher=None, on_attention=None, inspector=None):
        self.server, self.settings = server, settings
        self.launcher = launcher
        self.on_attention = on_attention or (lambda: None)
        self.inspector = inspector or inspect_companion
        self.stop = threading.Event(); self.wake = threading.Event()
        self.lock = threading.RLock(); self.process = None
        self.httpd = None; self.http_thread = None; self.thread = None
        self.identity = ''; self.remote_identity = ''; self.lease = ('', '')
        saved = self.settings.load_player_settings()
        self._enabled = saved.get(self.KEY, True) is not False; self._show_version = saved.get(self.VERSION_KEY) is True
        self.guide_acknowledged = saved.get(self.GUIDE_KEY) is True
        self.status = 'Off'; self.install_message = ''; self.install_busy = False
        self._last_start_error = ''
        self.next_attempt = 0.0

    def enabled(self): return self._enabled
    def show_version(self): return self._show_version
    def set_option(self, key, value):
        if key not in (self.KEY, self.VERSION_KEY, self.GUIDE_KEY) or type(value) is not bool: raise ValueError('Invalid setting')
        was_enabled = self._enabled
        self.settings.save_player_settings({key:value})
        if key == self.KEY: self._enabled = value
        elif key == self.VERSION_KEY: self._show_version = value
        else: self.guide_acknowledged = value
        self.next_attempt = 0; self.wake.set()
        if key == self.KEY and value and not was_enabled and self.thread is not None and not self.stop.is_set():
            threading.Thread(target=self._onboard, name='remote-lockscreen-setup', daemon=True).start()

    def start(self):
        if self.thread is not None: return
        controller = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if urlsplit(self.path).path != '/api/remote-tray/hello' or urlsplit(self.path).query != 'lockscreen=1':
                    self.send_error(404); return
                identity, remote_identity = controller.lease
                payload = status_payload(controller.server, identity, remote_identity, controller.show_version()) if identity else None
                if payload is None:
                    self.send_error(503, 'Remote player is unavailable'); return
                data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
                self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8')
                self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store')
                self.end_headers(); self.wfile.write(data)
            def log_message(self, *args): pass
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.httpd.daemon_threads = True
        self.http_thread = threading.Thread(target=self.httpd.serve_forever, name='remote-lockscreen-http', daemon=True)
        self.http_thread.start()
        self.thread = threading.Thread(target=self._run, name='remote-lockscreen', daemon=True)
        self.thread.start()
        threading.Thread(target=self._onboard, name='remote-lockscreen-setup', daemon=True).start()

    def _attention(self):
        if not self.stop.is_set():
            try: self.on_attention()
            except Exception: pass

    def _onboard(self):
        if not self.enabled() or self.stop.is_set(): return
        self.install_message = 'Checking Windows, the companion, and its certificate…'
        try:
            version, required, trusted, uac = self.inspector()
            if not self.enabled() or self.stop.is_set(): return
            if supported_version(version, required) and trusted:
                self.install_message = 'Companion verified (version ' + version + ').'
                if not self.guide_acknowledged: self._attention()
                return
            if uac is False and not trusted:
                self.install_message = 'User Account Control is off. Turn it on and restart Windows before installation; instructions are below.'
                self._attention(); return
            self.install_message = 'Installing the lock-screen companion automatically. Approve the Windows administrator prompt if it appears.'
            self._attention()
            self.install_async(automatic=True)
        except Exception as exc:
            self.install_message = 'Automatic check could not finish: ' + str(exc)[:500]
            self._attention()

    def _release(self):
        if self.process is not None:
            try: self.process.close()
            except (OSError, AttributeError): pass
            self.process = None
        self.identity = ''; self.remote_identity = ''; self.lease = ('', '')

    def _step(self):
        from PAFPlayer_lockscreen import installed_version, EMBEDDED_INSTALL_VERSION, launch
        if self.stop.is_set() or not self.enabled():
            self._release(); self.status = 'Off. Turn on status after installing the companion.'; return
        with self.server._lock:
            connected, remote_identity = self.server.connected, self.server.owner_identity
        if not connected or not remote_identity:
            self.status = 'Waiting for the remote PAFPlayer connection.'; return
        if self.process is not None and remote_identity != self.remote_identity:
            self._release(); self.next_attempt = 0
        if self.process is not None:
            code = self.process.poll()
            if code is None:
                self._last_start_error = ''
                self.status = 'Running. Windows controls what appears on the lock screen.'; return
            self._release(); self.status = f'Publisher stopped (code {code}); retrying.'
            self.next_attempt = time.monotonic() + 30
        if time.monotonic() < self.next_attempt: return
        self.next_attempt = time.monotonic() + 30
        if not supported_version(installed_version(), EMBEDDED_INSTALL_VERSION):
            self.status = 'Checking or installing the lock-screen companion.'; return
        self.identity = uuid.uuid4().hex; self.remote_identity = remote_identity
        self.lease = (self.identity, self.remote_identity)
        try:
            self.process = (self.launcher or launch)('http://127.0.0.1:%d' % self.httpd.server_port, self.identity)
            self.status = 'Starting lock-screen publisher.'
        except Exception:
            self.identity = ''; self.remote_identity = ''; self.lease = ('', '')
            raise

    def _run(self):
        try:
            while not self.stop.is_set():
                with self.lock:
                    try: self._step()
                    except Exception as exc:
                        self.status = 'Could not start: ' + str(exc)[:250]
                        if self.status != self._last_start_error:
                            self._last_start_error = self.status
                            self._attention()
                self.wake.wait(1); self.wake.clear()
        finally:
            with self.lock: self._release()

    def install_async(self, automatic=False):
        if self.install_busy: return False
        self.install_busy = True
        self.install_message = 'Installing. Approve the Windows administrator prompt if it appears.'
        def worker():
            try:
                from PAFPlayer_lockscreen import embedded_installer_root
                from PAFPlayer_lockscreen_installer import WindowsBackend, install
                with self.lock:
                    self._release()
                    code = install(embedded_installer_root(), WindowsBackend(), ask=lambda prompt:'yes')
                    self.install_message = ('Installed. Choose PAFPlayer in Windows Lock screen settings as explained below.'
                                            if code == 0 else 'Installation did not finish (code %s). Use Install or repair to retry.' % code)
            except Exception as exc:
                self.install_message = 'Installation failed: ' + str(exc)[:500]
            finally:
                self.install_busy = False; self.next_attempt = 0; self.wake.set()
                if automatic and ('failed' in self.install_message.casefold() or 'did not finish' in self.install_message.casefold() or not self.guide_acknowledged): self._attention()
        threading.Thread(target=worker, name='remote-lockscreen-install', daemon=True).start()
        return True

    def close(self):
        self.stop.set(); self.wake.set()
        if self.thread: self.thread.join(timeout=3)
        if self.httpd:
            self.httpd.shutdown(); self.httpd.server_close()
            if self.http_thread: self.http_thread.join(timeout=3)


def setup_dialog(controller, stop_event):
    """Present all steps locally; no install, lock, or settings change on open."""
    import tkinter as tk
    from tkinter import messagebox, ttk
    root = tk.Tk(); root.title('PAFPlayer — Lock screen setup'); root.geometry('670x590'); root.minsize(520, 430)
    frame = ttk.Frame(root, padding=16); frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Show the remote song on this computer’s lock screen', font=('Segoe UI', 13, 'bold'), wraplength=610).pack(anchor='w')
    text = ('PAFPlayer checks and installs the companion automatically. If Windows asks an administrator to approve the PAFPlayerLocal certificate, approve it to continue. If installation fails, use Install or repair below to retry.\n\n'
            'Keep “Show song status” on and leave this tray running and connected to the player.\n\n'
            '1. Click Open Windows Lock screen settings. Under “Choose one app to show detailed status”, '
            'choose “PAFPlayer Lock Screen V530”. If Windows offers quick status, choose the same app there for the playback icon.\n\n'
            '2. Click Test lock screen, or press Windows+L. Unlock normally with your PIN or password. '
            'Windows decides where and when the text appears.\n\n'
            'This companion requires 64-bit Windows 10 build 19041 or later. Windows 11 installation is allowed, but lock-screen display has not yet been verified there. '
            'The remote player must be reachable and this tray must remain running. If Windows says User Account Control is off, '
            'open Start, search for Change User Account Control settings, move the slider above Never notify, click OK, '
            'and restart Windows before trying Install again.')
    instructions = ttk.Frame(frame); instructions.pack(fill='both', expand=True, pady=12)
    scrollbar = ttk.Scrollbar(instructions); scrollbar.pack(side='right', fill='y')
    guide = tk.Text(instructions, height=12, wrap='word', font=('Segoe UI', 10), yscrollcommand=scrollbar.set)
    guide.pack(side='left', fill='both', expand=True); scrollbar.config(command=guide.yview)
    guide.insert('1.0', text); guide.configure(state='disabled')
    enabled = tk.BooleanVar(master=root, value=controller.enabled())
    version = tk.BooleanVar(master=root, value=controller.show_version())
    message = tk.StringVar(master=root, value='Checking status…')
    installed_text = tk.StringVar(master=root, value='Checking whether the companion is installed…')
    checks = queue.Queue(); last_install = [None]
    def check_installation():
        def check():
            try:
                from PAFPlayer_lockscreen import installed_version, EMBEDDED_INSTALL_VERSION
                found = installed_version()
                checks.put('Companion installed: ' + found if supported_version(found, EMBEDDED_INSTALL_VERSION) else
                           'Companion not installed or needs repair. Click Install or repair.')
            except Exception as exc: checks.put('Could not check installation: ' + str(exc))
        threading.Thread(target=check, name='remote-lockscreen-check', daemon=True).start()
    check_installation()
    def save(key, var):
        try: controller.set_option(key, bool(var.get()))
        except Exception as exc: messagebox.showerror('Could not save setting',str(exc),parent=root)
    ttk.Checkbutton(frame,text='Show song status on this computer',variable=enabled,command=lambda:save(controller.KEY,enabled)).pack(anchor='w')
    ttk.Checkbutton(frame,text='Include player version',variable=version,command=lambda:save(controller.VERSION_KEY,version)).pack(anchor='w')
    buttons = ttk.Frame(frame); buttons.pack(fill='x', pady=10)
    def install():
        consent = messagebox.askyesno('Install lock-screen companion',
            'The companion uses the bundled PAFPlayerLocal certificate. Windows may ask an administrator to trust it for this computer. Continue?', parent=root)
        if consent: controller.install_async()
    install_button = ttk.Button(buttons,text='Install or repair',command=install)
    install_button.pack(side='left',padx=(0,6))
    def open_settings():
        try: os.startfile('ms-settings:lockscreen')
        except OSError as exc: messagebox.showerror('Could not open Settings',str(exc),parent=root)
    ttk.Button(buttons,text='1. Open Windows settings',command=open_settings).pack(side='left',padx=6)
    def test():
        if messagebox.askyesno('Test lock screen','Lock this computer now? You will need your normal PIN or password to unlock.',parent=root):
            try:
                from PAFPlayer_lockscreen import lock_workstation
                lock_workstation()
            except OSError as exc: messagebox.showerror('Could not lock',str(exc),parent=root)
    ttk.Button(buttons,text='2. Test lock screen',command=test).pack(side='left',padx=6)
    ttk.Label(frame,textvariable=installed_text,wraplength=610,justify='left').pack(fill='x')
    ttk.Label(frame,textvariable=message,wraplength=610,justify='left').pack(fill='x',pady=8)
    def acknowledge():
        try: controller.set_option(controller.GUIDE_KEY, True)
        except Exception as exc:
            messagebox.showerror('Could not save setting', str(exc), parent=root); return
        root.destroy()
    ttk.Button(frame,text='I selected PAFPlayer in Windows',command=acknowledge).pack(anchor='e')
    ttk.Button(frame,text='Close',command=root.destroy).pack(anchor='e')
    def poll():
        if stop_event.is_set(): root.destroy(); return
        try:
            while True: installed_text.set(checks.get_nowait())
        except queue.Empty: pass
        install_button.configure(state='disabled' if controller.install_busy else 'normal')
        if last_install[0] is True and not controller.install_busy: check_installation()
        last_install[0] = controller.install_busy
        message.set('Status: ' + controller.status + ('\n' + controller.install_message if controller.install_message else ''))
        root.after(500,poll)
    poll(); root.mainloop()
