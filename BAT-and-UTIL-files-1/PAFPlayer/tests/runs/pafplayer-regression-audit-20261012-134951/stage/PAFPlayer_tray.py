"""Windows notification-area control owned by the verified PAFPlayer instance."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import threading
import time
import webbrowser

CLICK_WINDOW_SECONDS = 0.50


def parse_options(arguments):
    """Remove session-only tray/instance switches before the playback parser."""
    remaining, override, explicit = [], None, False
    for argument in arguments:
        if argument == '--tray': override = True
        elif argument == '--no-tray': override = False
        elif argument == '--instance': explicit = True
        else: remaining.append(argument)
    return remaining, override, explicit


def enabled(saved, override=None):
    return bool(saved.get('TrayIconEnabled', 1)) if override is None else override


def configure(runtime, payload):
    if set(payload) != {'enabled'} or type(payload['enabled']) is not bool:
        raise ValueError('Expected a tray enabled checkbox value')
    runtime.app.save_player_settings({'TrayIconEnabled': int(payload['enabled'])})
    if getattr(runtime, 'tray', None): runtime.tray.refresh()
    return runtime.tray.status() if getattr(runtime, 'tray', None) else {'saved_enabled': payload['enabled']}


HTML = '''
<div class="group" id="trayIconSection"><h3>Windows tray icon</h3>
<p>One icon follows the official PAFPlayer instance. Triple-left-click: previous track. Triple-right-click: next track. Double-click either button: Play/Pause after the click window. A single right-click opens the menu after the click window.</p>
<label><input id="trayIconEnabled" type="checkbox" disabled> Enable tray icon by default</label>
<p id="trayIconStatus" role="status">Loading tray status…</p></div>
'''
SCRIPT = r'''
<script>(()=>{
 const box=document.getElementById('trayIconEnabled'),status=document.getElementById('trayIconStatus');let token='',busy=false;
 function show(v){box.checked=!!v.saved_enabled;box.disabled=false;status.textContent=(v.visible?'Icon visible':'No icon in this instance')+' · '+(v.instance==='official'?'Official instance owns the tray':'Additional instance; official instance owns the tray')+(v.override===null?'':' · command-line override for this run')}
 async function poll(){if(busy)return;try{const r=await fetch('/api/workflows/status',{cache:'no-store'}),v=await r.json();if(!r.ok)throw Error(v.error);if(v.local)token=v.token;show(v.tray);if(!v.local)box.disabled=true}catch(e){status.textContent=String(e)}}
 box.onchange=async()=>{busy=true;try{const r=await fetch('/api/workflows/tray',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify({enabled:box.checked})}),v=await r.json();if(!r.ok)throw Error(v.error);show(v)}catch(e){status.textContent=String(e)}finally{busy=false}};
 poll();setInterval(()=>{if(!document.hidden)poll()},3000);
})();</script>
'''

CONTROL_HTML = '''
<div class="group" id="controlSection"><h3>Control</h3>
<label><input id="controlHotkeysEnabled" type="checkbox" disabled> Enable Windows control hotkeys on this player</label>
<p>Ctrl+Alt+Up/Down adjusts volume; Ctrl+Alt+A brings album art forward; Ctrl+Alt+F controls floating lyrics; Win+C pauses or resumes. Media keys work while another window is active. On tray-only computers, these keys relay actions to this player; Ctrl+Shift+Alt+F/A instead toggle lyrics/art windows on that computer.</p>
<p id="controlHotkeysStatus" role="status">Loading control setting…</p></div>
'''
CONTROL_SCRIPT = r'''\n<script>(()=>{const box=document.getElementById('controlHotkeysEnabled'),status=document.getElementById('controlHotkeysStatus');let token='',busy=false;\nasync function poll(){if(busy)return;try{const r=await fetch('/api/workflows/status',{cache:'no-store'}),v=await r.json();if(!r.ok)throw Error(v.error);token=v.local?v.token:'';box.checked=!!v.control.hotkeys_enabled;box.disabled=!v.local;status.textContent=v.local?'Saved on this player':'Change this on the player computer'}catch(e){status.textContent=String(e)}}\nbox.onchange=async()=>{busy=true;try{const r=await fetch('/api/workflows/control',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify({hotkeys_enabled:box.checked})}),v=await r.json();if(!r.ok)throw Error(v.error);box.checked=v.hotkeys_enabled;status.textContent='Setting saved'}catch(e){status.textContent=String(e)}finally{busy=false}};poll();setInterval(()=>{if(!document.hidden)poll()},3000)})();</script>\n'''

def augment(page):
    return page.replace('<div class="group section-global-config" id="globalConfigSection">',
                        HTML + CONTROL_HTML + '<div class="group section-global-config" id="globalConfigSection">', 1).replace('</body>', SCRIPT + CONTROL_SCRIPT + '</body>', 1)


class ClickSequence:
    """Count button releases; Windows double-click messages are deliberately ignored."""
    def __init__(self, window=CLICK_WINDOW_SECONDS):
        self.window = window
        self.button = None
        self.count = 0
        self.last = 0.0

    def click(self, button, now):
        if button != self.button or now - self.last > self.window:
            self.button, self.count = button, 0
        self.count += 1
        self.last = now
        if self.count == 3:
            self.button, self.count = None, 0
            return 'previous' if button == 'left' else 'next'
        return None

    def expire(self, now):
        if self.button is None or now - self.last + 1e-9 < self.window:
            return None
        action = 'pause' if self.count == 2 else 'menu' if self.button == 'right' and self.count == 1 else None
        self.button, self.count = None, 0
        return action


class TrayController:
    WM_TRAY = 0x8000 + 41
    WM_SYNC = 0x8000 + 42
    WM_TIMER = 0x0113
    WM_CLOSE = 0x0010
    WM_DESTROY = 0x0002
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONUP = 0x0205
    WM_MOUSEMOVE = 0x0200
    NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
    NIF_MESSAGE, NIF_ICON, NIF_TIP = 1, 2, 4

    def __init__(self, runtime, instance, override=None, *, click_window=CLICK_WINDOW_SECONDS):
        self.runtime, self.instance, self.override = runtime, instance, override
        if os.name == 'nt' and click_window == CLICK_WINDOW_SECONDS:
            click_window = max(.35, min(.9, ctypes.windll.user32.GetDoubleClickTime() / 1000))
        self.clicks = ClickSequence(click_window)
        self._lock = threading.RLock()
        self._thread = None
        self._hwnd = None
        self._visible = False
        self._closing = False
        self._ready = threading.Event()
        self._taskbar_created = 0
        self._machine = None
        self._hover = None
        self._hover_art_key = None

    def attach_machine_options(self, *, remote=False):
        if self._machine is None:
            from PAFPlayer_tray_machine import TrayMachineEffects
            self._machine = TrayMachineEffects(self.runtime.server, self.instance, self.refresh,
                                               remote=remote)
        return self._machine

    def wants_icon(self):
        # The registry is the existing global player setting store. A CLI
        # override never writes to it and remains effective for this run.
        return enabled(self.runtime.app.load_player_settings(), self.override)

    def status(self):
        with self._lock:
            return {'enabled': self.wants_icon(), 'saved_enabled': enabled(self.runtime.app.load_player_settings()),
                    'override': self.override, 'owner': 'official' if self.instance.owns() else 'another instance',
                    'visible': self._visible, 'instance': 'official' if self.instance.owns() else 'additional'}

    def start(self):
        if os.name != 'nt' or not self.instance.owns(): return False
        with self._lock:
            if self._closing: return False
            if self._thread and self._thread.is_alive():
                self.refresh()
                return True
            self._ready.clear()
            self._thread = threading.Thread(target=self._run, name='paf-tray', daemon=True)
            self._thread.start()
        self._ready.wait(2)
        if self._hwnd and self._machine:
            self._machine.start()
        return bool(self._hwnd)

    def refresh(self):
        if self._hwnd and os.name == 'nt':
            ctypes.windll.user32.PostMessageW(self._hwnd, self.WM_SYNC, 0, 0)

    def close(self):
        with self._lock:
            self._closing = True
            hwnd, thread = self._hwnd, self._thread
        if hwnd and os.name == 'nt': ctypes.windll.user32.PostMessageW(hwnd, self.WM_CLOSE, 0, 0)
        if thread and thread is not threading.current_thread(): thread.join(timeout=3)
        if self._machine:
            self._machine.close()

    def dispatch(self, action):
        """Every action is local to the mutex owner and its own playback queue."""
        if not self.instance.owns() or self._closing: return False
        if action.startswith('machine_') and self._machine:
            return self._machine.toggle(action.removeprefix('machine_'))
        server = self.runtime.server
        if action in ('previous', 'next', 'pause'):
            if not server: return False
            mapping = {'previous': self.runtime.app.PREVIOUS_FILE,
                       'next': self.runtime.app.NEXT_FILE,
                       'pause': self.runtime.app.PAUSE_TOGGLE}
            return server.enqueue_action(mapping[action])
        if action == 'exit':
            if not server: return False
            server.enqueue_tray_exit()
            return True
        if action == 'web':
            if server and server.enabled and server._httpd:
                webbrowser.open(server.url)
                return True
            self._message('Web configuration is disabled for this run.')
            return False
        if action == 'details':
            if server and server.enabled and server._httpd:
                from PAFPlayer_remote_tray import launch_viewer
                launch_viewer(server.url)
                return True
            self._message('The tag viewer requires the web server to be enabled for this run.')
            return False
        if action == 'folder':
            path = server.current_audio() if server else None
            if path and path.parent.is_dir():
                os.startfile(str(path.parent))
                return True
            return False
        if action == 'about':
            message = 'PAFPlayer ' + self.runtime.app.PROGRAM_VERSION + '\nOfficial instance (PID ' + str(os.getpid()) + ')'
            if self._machine and self._machine.last_error:
                message += '\nDesktop option: ' + self._machine.last_error
            self._message(message)
            return True
        return False

    def tooltip_text(self):
        base = 'PAFPlayer ' + self.runtime.app.PROGRAM_VERSION + ' · official PID ' + str(os.getpid())
        lyric = self._machine.tooltip_lyric() if self._machine else ''
        return base + (' · ' + lyric if lyric else '')

    def menu_items(self, state):
        label = 'Play' if state.get('paused') else 'Pause'
        folder = bool(self.runtime.server and self.runtime.server.current_audio())
        return [(1, label, 'pause', True), (2, 'Previous track', 'previous', True),
                (3, 'Next track', 'next', True), (4, 'Open web configuration', 'web', True),
                (5, 'Open tag viewer', 'details', True),
                (6, ('✓ ' if self._machine and self._machine.options['lyrics_tooltip'] else '○ ') + 'Live lyrics in tooltip', 'machine_lyrics_tooltip', True),
                (7, ('✓ ' if self._machine and self._machine.options['album_wallpaper'] else '○ ') + 'Album art desktop wallpaper', 'machine_album_wallpaper', True),
                (8, 'Open current track folder', 'folder', folder),
                (9, 'About / version', 'about', True), (10, 'Exit PAFPlayer', 'exit', True)]

    def poll_hotkeys(self):
        """Tray-only overrides this without blocking the Win32 message pump."""
        return None

    def _refresh_hover_art(self, state):
        if not self._hover: return
        key = (getattr(self.runtime.server, 'owner_identity', ''),
               state.get('art_generation'), state.get('art_count'))
        if key == self._hover_art_key: return
        self._hover_art_key = key
        self._hover.set_bitmap(None)
        if not state.get('art_count'): return
        def fetch():
            try:
                server = self.runtime.server
                if hasattr(server, 'wallpaper'):
                    data = server.wallpaper(int(state['art_generation']), 320, 240)
                else:
                    from PAFPlayer_track_details import wallpaper_bitmap
                    art, _mime = server.art_snapshot_at_generation(int(state['art_generation']), 0)
                    data = wallpaper_bitmap(art, 320, 240) if art else None
                if self._hover_art_key == key and self._hover:
                    self._hover.set_bitmap(data)
            except (OSError, ValueError, TypeError): pass
        threading.Thread(target=fetch, name='paf-tray-hover-art', daemon=True).start()

    def _message(self, text):
        if os.name == 'nt':
            user32 = ctypes.windll.user32
            user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
            user32.MessageBoxW(self._hwnd, text, 'PAFPlayer', 0)

    def _run(self):
        user32, shell32, kernel32 = ctypes.windll.user32, ctypes.windll.shell32, ctypes.windll.kernel32
        LRESULT = ctypes.c_ssize_t
        WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

        class WNDCLASSW(ctypes.Structure):
            _fields_ = [('style', wintypes.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', ctypes.c_int),
                        ('cbWndExtra', ctypes.c_int), ('hInstance', wintypes.HINSTANCE), ('hIcon', wintypes.HICON),
                        ('hCursor', wintypes.HANDLE), ('hbrBackground', wintypes.HANDLE),
                        ('lpszMenuName', wintypes.LPCWSTR), ('lpszClassName', wintypes.LPCWSTR)]

        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [('cbSize', wintypes.DWORD), ('hWnd', wintypes.HWND), ('uID', wintypes.UINT),
                        ('uFlags', wintypes.UINT), ('uCallbackMessage', wintypes.UINT), ('hIcon', wintypes.HICON),
                        ('szTip', wintypes.WCHAR * 128), ('dwState', wintypes.DWORD), ('dwStateMask', wintypes.DWORD),
                        ('szInfo', wintypes.WCHAR * 256), ('uTimeoutOrVersion', wintypes.UINT),
                        ('szInfoTitle', wintypes.WCHAR * 64), ('dwInfoFlags', wintypes.DWORD),
                        ('guidItem', ctypes.c_byte * 16), ('hBalloonIcon', wintypes.HICON)]

        shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
        shell32.Shell_NotifyIconW.restype = wintypes.BOOL
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.LoadIconW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR]
        user32.DefWindowProcW.restype = LRESULT
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                           wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                           wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.LoadIconW.restype = wintypes.HICON
        user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
        user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        user32.SetTimer.argtypes = [wintypes.HWND, ctypes.c_size_t, wintypes.UINT, ctypes.c_void_p]
        user32.KillTimer.argtypes = [wintypes.HWND, ctypes.c_size_t]
        user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.TrackPopupMenuEx.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int,
                                            wintypes.HWND, ctypes.c_void_p]
        user32.DestroyMenu.argtypes = [wintypes.HMENU]
        user32.DestroyWindow.argtypes = [wintypes.HWND]
        user32.CreatePopupMenu.restype = wintypes.HMENU
        user32.TrackPopupMenuEx.restype = wintypes.UINT
        icon = user32.LoadIconW(None, ctypes.cast(ctypes.c_void_p(32516), wintypes.LPCWSTR))  # IDI_INFORMATION
        name = 'PAFPlayerTray-' + str(os.getpid())
        notify = NOTIFYICONDATAW()
        notify.cbSize = ctypes.sizeof(notify)
        notify.uID = 1
        notify.uFlags = self.NIF_MESSAGE | self.NIF_ICON | self.NIF_TIP
        notify.uCallbackMessage = self.WM_TRAY
        notify.hIcon = icon
        notify.szTip = self.tooltip_text()[:127]
        self._taskbar_created = user32.RegisterWindowMessageW('TaskbarCreated')

        last_sync = 0.0
        def sync():
            nonlocal last_sync
            last_sync = time.monotonic()
            should_show = self.instance.owns() and not self._closing and self.wants_icon()
            tip = self.tooltip_text()[:127]
            if notify.szTip != tip:
                notify.szTip = tip
                if self._visible:
                    shell32.Shell_NotifyIconW(self.NIM_MODIFY, ctypes.byref(notify))
            if should_show and not self._visible:
                self._visible = bool(shell32.Shell_NotifyIconW(self.NIM_ADD, ctypes.byref(notify)))
            elif not should_show and self._visible:
                shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(notify))
                self._visible = False

        def menu():
            if not self.instance.owns() or not self._visible: return
            popup = user32.CreatePopupMenu()
            try:
                state = self.runtime.server.snapshot() if self.runtime.server else {}
                items = self.menu_items(state)
                for number, title, _action, active in items:
                    checked = title.startswith('✓ ')
                    checkable = checked or title.startswith('○ ')
                    flags = (0 if active else 0x0002) | (0x0008 if checked else 0)
                    user32.AppendMenuW(popup, flags, number, title[2:] if checkable else title)
                position = wintypes.POINT()
                user32.GetCursorPos(ctypes.byref(position))
                user32.SetForegroundWindow(notify.hWnd)
                selected = user32.TrackPopupMenuEx(popup, 0x0100 | 0x0002, position.x, position.y, notify.hWnd, None)
                user32.PostMessageW(notify.hWnd, 0, 0, 0)
                actions = {number: action for number, _title, action, _active in items}
                if selected in actions: self.dispatch(actions[selected])
            finally:
                user32.DestroyMenu(popup)

        @WNDPROC
        def wndproc(hwnd, message, wparam, lparam):
            if message == self.WM_TRAY:
                if lparam == self.WM_MOUSEMOVE and self._visible and self._hover:
                    state = self.runtime.server.snapshot() if self.runtime.server else {}
                    self._hover.show(state)
                    self._refresh_hover_art(state)
                if lparam in (self.WM_LBUTTONUP, self.WM_RBUTTONUP):
                    if self._hover: self._hover.hide()
                    action = self.clicks.click('left' if lparam == self.WM_LBUTTONUP else 'right', time.monotonic())
                    if action: self.dispatch(action)
                return 0
            if message == self.WM_SYNC:
                sync(); return 0
            if message == self.WM_TIMER:
                self.poll_hotkeys()
                if self._hover: self._hover.tick()
                action = self.clicks.expire(time.monotonic())
                if action == 'menu': menu()
                elif action == 'pause': self.dispatch('pause')
                if time.monotonic() - last_sync >= 2: sync()
                return 0
            if message == self._taskbar_created:
                self._visible = False; sync(); return 0
            if message == self.WM_CLOSE:
                user32.DestroyWindow(hwnd)
                return 0
            if message == self.WM_DESTROY:
                if self._visible: shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(notify))
                if self._hover: self._hover.close(); self._hover = None
                self._visible = False
                user32.KillTimer(hwnd, 1)
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, message, wparam, lparam)

        klass = WNDCLASSW()
        klass.lpfnWndProc = wndproc
        klass.hInstance = kernel32.GetModuleHandleW(None)
        klass.lpszClassName = name
        if not user32.RegisterClassW(ctypes.byref(klass)):
            self._ready.set(); return
        hwnd = user32.CreateWindowExW(0, name, name, 0, 0, 0, 0, 0, None, None, klass.hInstance, None)
        if not hwnd:
            self._ready.set(); return
        notify.hWnd = hwnd
        self._hwnd = hwnd
        from PAFPlayer_tray_hover import HoverCard
        self._hover = HoverCard(hwnd, notify.uID, name)
        user32.SetTimer(hwnd, 1, 50, None)
        sync()
        self._ready.set()
        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
        self._hwnd = None
