"""Local Steam activity and visual-only load controls; no audio/process control."""
from __future__ import annotations

import atexit
import ctypes
from ctypes import wintypes
import ntpath
import os
from pathlib import Path
import re
import threading
import time

REDUCE = 'SteamReduceVisualizerLoad'
NO_GALLERY = 'SteamDisableIdleGallery'
DEFAULTS = {REDUCE: 1, NO_GALLERY: 1}


def process_images():
    """Read process paths with limited query access; never inspect process memory."""
    if os.name != 'nt':
        return []
    class Entry(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                    ('pid', wintypes.DWORD), ('heap', ctypes.c_size_t),
                    ('module', wintypes.DWORD), ('threads', wintypes.DWORD),
                    ('parent', wintypes.DWORD), ('priority', wintypes.LONG),
                    ('flags', wintypes.DWORD), ('name', wintypes.WCHAR * 260)]
    # Private DLL wrapper: avoid changing prototypes used by other player modules.
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    api.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    for name in ('Process32FirstW', 'Process32NextW'):
        func = getattr(api, name)
        func.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
        func.restype = wintypes.BOOL
    api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    api.OpenProcess.restype = wintypes.HANDLE
    api.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                              wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    api.QueryFullProcessImageNameW.restype = wintypes.BOOL
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    snapshot = api.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    result = []
    try:
        entry = Entry(); entry.dwSize = ctypes.sizeof(entry)
        more = api.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            handle = api.OpenProcess(0x1000, False, entry.pid)
            path = ''
            if handle:
                try:
                    buffer = ctypes.create_unicode_buffer(32768)
                    size = wintypes.DWORD(len(buffer))
                    if api.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                        path = buffer.value
                finally:
                    api.CloseHandle(handle)
            result.append({'pid': int(entry.pid), 'name': entry.name, 'exe': path})
            more = api.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        api.CloseHandle(snapshot)
    return result


def steam_registry():
    """Steam's local Running flags are supplementary, undocumented client state."""
    paths, running = [], []
    if os.name != 'nt': return paths, running
    import winreg
    for hive, subkey, value in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                               (winreg.HKEY_LOCAL_MACHINE, r'Software\WOW6432Node\Valve\Steam', 'InstallPath')):
        try:
            with winreg.OpenKey(hive, subkey) as key:
                paths.append(str(winreg.QueryValueEx(key, value)[0]))
        except OSError: pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam\Apps') as apps:
            for index in range(min(10000, winreg.QueryInfoKey(apps)[0])):
                appid = winreg.EnumKey(apps, index)
                if not appid.isdecimal(): continue
                try:
                    with winreg.OpenKey(apps, appid) as key:
                        if int(winreg.QueryValueEx(key, 'Running')[0]) == 1:
                            running.append(appid)
                except (OSError, ValueError, TypeError): pass
    except OSError: pass
    return paths, running


def read_vdf(path):
    with Path(path).open('r', encoding='utf-8-sig', errors='replace') as stream:
        return stream.read(2 * 1024 * 1024)


def catalog(roots):
    """Discover installed app directories; bounded, periodically cached disk work."""
    libraries = set(str(Path(root)) for root in roots if root)
    for root in tuple(libraries):
        try:
            text = read_vdf(Path(root) / 'steamapps' / 'libraryfolders.vdf')
            libraries.update(value.replace('\\\\', '\\') for value in
                             re.findall(r'"path"\s*"([^"\r\n]+)"', text, re.I))
        except OSError: pass
    result = {}
    for root in sorted(libraries)[:32]:
        folder = Path(root) / 'steamapps'
        try:
            for index, manifest in enumerate(folder.glob('appmanifest_*.acf')):
                if index >= 10000: break
                try:
                    fields = dict(re.findall(r'"(appid|name|installdir)"\s*"([^"\r\n]+)"', read_vdf(manifest)))
                    appid, directory = fields.get('appid', ''), fields.get('installdir', '')
                    if not appid.isdecimal() or not directory or directory in ('.', '..') or any(c in directory for c in '\\/:'):
                        continue
                    result[appid] = {'name': fields.get('name', 'Steam app ' + appid),
                                     'directory': str(folder / 'common' / directory)}
                except OSError: pass
        except OSError: pass
    return result


def detect_games(processes, apps, running_ids):
    steam_alive = any(p['name'].casefold() == 'steam.exe' for p in processes)
    found = set()
    # Redistributable installers are not games, even when launched from a game folder.
    excluded = {'steam.exe', 'steamwebhelper.exe', 'gameoverlayui.exe', 'steamservice.exe',
                'dxsetup.exe', 'vc_redist.x64.exe', 'vc_redist.x86.exe', 'vcredist_x64.exe',
                'vcredist_x86.exe', 'crashpad_handler.exe', 'crashreportclient.exe'}
    directories = [(appid, ntpath.normcase(ntpath.normpath(info['directory'])) + '\\')
                   for appid, info in apps.items() if appid != '228980']
    for process in processes:
        if process['name'].casefold() in excluded: continue
        path = ntpath.normcase(ntpath.normpath(process.get('exe') or ''))
        if '\\_commonredist\\' in path: continue
        for appid, directory in directories:
            if path.startswith(directory): found.add(appid)
    if steam_alive:
        found.update(str(appid) for appid in running_ids if str(appid) != '228980')
    return tuple(sorted(apps.get(appid, {}).get('name', 'Steam app ' + appid) for appid in found))


class Monitor:
    def __init__(self, app, *, processes=process_images, registry=steam_registry, inventory=catalog):
        self.app, self.processes, self.registry, self.inventory = app, processes, registry, inventory
        self.stop = threading.Event()
        self._thread = None
        self._apps, self._roots, self._catalog_at = {}, (), -1e9
        self._options = dict(DEFAULTS)
        self._lock = threading.Lock()
        self._state = (0.0, (), 'Checking Steam activity…')

    def tick(self):
        with self._lock:
            settings = self.app.load_player_settings()
            self._options = {key: bool(settings.get(key, 1)) for key in DEFAULTS}
        if not any(self._options.values()):
            self._state = (time.monotonic(), (), 'Steam checks disabled')
            return
        processes = self.processes()
        roots, running = self.registry()
        roots += [ntpath.dirname(p['exe']) for p in processes
                  if p['name'].casefold() == 'steam.exe' and p.get('exe')]
        roots = tuple(sorted(set(roots)))
        now = time.monotonic()
        if roots != self._roots or now - self._catalog_at >= 60:
            self._apps = self.inventory(roots)
            self._roots, self._catalog_at = roots, now
        games = detect_games(processes, self._apps, running)
        self._state = (time.monotonic(), games, 'Steam game running' if games else 'No running Steam game detected')

    def _run(self):
        while not self.stop.is_set():
            try: self.tick()
            except Exception as exc:
                self._state = (time.monotonic(), (), 'Steam detection unavailable: ' + type(exc).__name__)
            self.stop.wait(2.0)

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name='paf-steam-monitor', daemon=True)
            self._thread.start()
        return self

    def running(self):
        updated, games, _ = self._state
        return bool(games) and time.monotonic() - updated < 8.0

    def visualizer_fps(self, fps):
        return float(fps) * (.5 if self._options[REDUCE] and self.running() else 1.0)

    def block_gallery(self):
        return bool(self._options[NO_GALLERY] and self.running())

    def status(self):
        return {'settings': dict(self._options), 'playing': self.running(),
                'games': list(self._state[1]) if self.running() else [], 'status': self._state[2]}

    def configure(self, payload):
        if not isinstance(payload, dict) or not payload or any(k not in DEFAULTS or type(v) is not bool for k, v in payload.items()):
            raise ValueError('Expected Steam checkbox values')
        with self._lock:
            self.app.save_player_settings({k: int(v) for k, v in payload.items()})
            self._options = dict(self._options, **payload)
        return self.status()

    def close(self):
        self.stop.set()
        if self._thread and self._thread is not threading.current_thread(): self._thread.join(timeout=3)


_monitor = None
_monitor_lock = threading.Lock()


def get_monitor(app):
    global _monitor
    if _monitor is None:
        with _monitor_lock:
            if _monitor is None:
                _monitor = Monitor(app).start()
                atexit.register(_monitor.close)
    return _monitor


def augment(page):
    html = '''<div class="group" id="steamSection"><h3>Steam</h3>
<label><input type="checkbox" id="steamReduce" checked>Reduce visualizer load by 50% if Steam game is playing</label>
<label><input type="checkbox" id="steamGallery" checked>Do not run idle artwork gallery if Steam game is playing</label>
<p class="note">Halves the console visualizer’s frame budget; audio and lyric timing stay unchanged. A game can be in the background. Steam simply being open does not count. Settings are saved for future runs.</p>
<p id="steamStatus" role="status"></p></div>'''
    script = '''<script>(()=>{
const reduce=document.getElementById('steamReduce'),gallery=document.getElementById('steamGallery'),status=document.getElementById('steamStatus');let busy=false,token='';
async function request(payload){const r=await fetch('/api/workflows/steam',payload===undefined?{cache:'no-store'}:{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw new Error(data.error||r.statusText);return data}
function show(data){token=data.token||token;reduce.checked=!!data.settings.SteamReduceVisualizerLoad;gallery.checked=!!data.settings.SteamDisableIdleGallery;reduce.disabled=gallery.disabled=!data.local;status.textContent=data.status+(data.games.length?' · '+data.games.join(', '):'')+(!data.local?' · Change these settings on the player computer.':'')}
async function refresh(){if(busy)return;try{show(await request())}catch(e){status.textContent=String(e)}}
async function change(key,control){busy=true;reduce.disabled=gallery.disabled=true;try{show(await request({[key]:control.checked}))}catch(e){status.textContent=String(e)}finally{busy=false;await refresh()}}
reduce.onchange=()=>change('SteamReduceVisualizerLoad',reduce);gallery.onchange=()=>change('SteamDisableIdleGallery',gallery);refresh();setInterval(()=>{if(!document.hidden)refresh()},3000);
})();</script>'''
    anchor = '<div class="group section-global-config" id="globalConfigSection">'
    return page.replace(anchor, html + anchor, 1).replace('</body>', script + '</body>', 1)
