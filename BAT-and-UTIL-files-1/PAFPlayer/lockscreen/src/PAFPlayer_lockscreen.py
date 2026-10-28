"""PAFPlayer-owned, optional Windows lock-screen publisher lifecycle.

Bundled into PAFPlayer.py. All Windows activation and process work stays on one
daemon worker; the audio/render loops never wait for the companion.
"""
from __future__ import annotations
import base64
import ctypes
import ipaddress
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid
from urllib.parse import parse_qs, urlsplit
from bisect import bisect_right

KEY = 'PAFPlayerLockScreenEnabled'
VERSION_KEY = 'PAFPlayerLockScreenShowVersion'
FAMILY = 'ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2'
THUMBPRINT = '08AC642F1C17B503BC857189AE8C78E76B3358EC'
EMBEDDED_INSTALL_VERSION = '530.0.0.0'
AUTO_INSTALL_MARKER = 'lockscreen-auto-install-v530.attempted'
DEFERRED_INSTALL_MARKER = 'lockscreen-install-user-requested.pending'


def deferred_install_path():
    return Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'PAFPlayer' / DEFERRED_INSTALL_MARKER


def request_deferred_install():
    """Remember an explicit install request for the first UAC-enabled run."""
    marker = deferred_install_path()
    if marker.exists():
        return marker
    marker.parent.mkdir(parents=True, exist_ok=True)
    try:
        with marker.open('x', encoding='utf-8') as stream:
            stream.write('Explicit lock-screen install requested; retry after UAC becomes available.\n')
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        pass
    return marker


def embedded_installer_root():
    """Materialize verified bundled bytes in a versioned, reusable user cache."""
    from PAFPlayer_lockscreen_payload import PAYLOAD_SHA256, payload_bytes
    local = Path(os.environ.get('LOCALAPPDATA') or Path.home())
    root = local / 'PAFPlayer' / 'LockScreenInstaller' / ('v' + EMBEDDED_INSTALL_VERSION.split('.')[0])
    paths = {
        'PAFPlayerLockScreen_v530_x64.msix': root / 'dist/v530/PAFPlayerLockScreen_v530_x64.msix',
        'PAFPlayerLockScreen_v505.cer': root / 'dist/PAFPlayerLockScreen_v505.cer',
    }
    import hashlib
    for name, path in paths.items():
        data = payload_bytes(name)
        expected = PAYLOAD_SHA256[name]
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        # Never overwrite an unexpected file. A damaged/tampered cache gets a
        # new collision-safe cache root and the original remains recoverable.
        if path.exists():
            root = root.with_name(root.name + '-' + uuid.uuid4().hex[:8])
            return embedded_installer_root_at(root)
        with path.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise OSError('Embedded lock-screen payload verification failed: ' + name)
    return root


def embedded_installer_root_at(root):
    """Write the payload to an already-selected collision-safe cache root."""
    from PAFPlayer_lockscreen_payload import PAYLOAD_SHA256, payload_bytes
    import hashlib
    root = Path(root)
    paths = {
        'PAFPlayerLockScreen_v530_x64.msix': root / 'dist/v530/PAFPlayerLockScreen_v530_x64.msix',
        'PAFPlayerLockScreen_v505.cer': root / 'dist/PAFPlayerLockScreen_v505.cer',
    }
    for name, path in paths.items():
        data = payload_bytes(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        if hashlib.sha256(path.read_bytes()).hexdigest() != PAYLOAD_SHA256[name]:
            raise OSError('Embedded lock-screen payload verification failed: ' + name)
    return root


def install_embedded_lockscreen(*, check_only=False, ask=input, backend=None):
    """Install/update the companion using only bytes bundled in PAFPlayer.py."""
    if os.name != 'nt':
        print('Lock-screen installation requires Windows 10.', file=sys.stderr)
        return 1
    from PAFPlayer_lockscreen_installer import WindowsBackend, install
    try:
        return install(embedded_installer_root(), backend or WindowsBackend(),
                       check_only=check_only, ask=ask)
    except Exception as error:
        print('Lock-screen installer stopped: ' + str(error), file=sys.stderr)
        return 1


def maybe_auto_install_lockscreen():
    """Attempt the bundled installer once for this release on normal first run."""
    if os.name != 'nt':
        return 0
    if deferred_install_path().is_file():
        if installed_version() == EMBEDDED_INSTALL_VERSION or uac_enabled() is False:
            return 0
        print('🪟 Retrying the user-requested lock-screen installation after UAC became available.')
        return install_embedded_lockscreen(ask=lambda _prompt: 'yes')
    local = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'PAFPlayer'
    marker = local / AUTO_INSTALL_MARKER
    if marker.exists():
        return 0
    local.mkdir(parents=True, exist_ok=True)
    try:
        with marker.open('x', encoding='utf-8') as stream:
            stream.write('PAFPlayer V530 first-run lock-screen install attempted\n')
    except FileExistsError:
        return 0
    from PAFPlayer_lockscreen_installer import WindowsBackend
    try:
        if WindowsBackend().installed_version() == EMBEDDED_INSTALL_VERSION:
            return 0
    except Exception:
        pass
    print('🪟 First-run lock-screen setup: installing/updating the bundled V530 companion.')
    # First-run setup is already an explicit product action. Go straight to
    # Windows' required UAC consent instead of depending on a console prompt.
    return install_embedded_lockscreen(ask=lambda _prompt: 'yes')


def uac_enabled():
    """Return Windows UAC policy, or None when policy cannot be read."""
    if os.name != 'nt':
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System') as key:
            return bool(int(winreg.QueryValueEx(key, 'EnableLUA')[0]))
    except (OSError, TypeError, ValueError):
        return None


def installed_version():
    if os.name != 'nt':
        return ''
    try:
        from PAFPlayer_lockscreen_installer import WindowsBackend
        return str(WindowsBackend().installed_version() or '')
    except Exception:
        return ''


def lock_workstation():
    if os.name != 'nt' or not ctypes.windll.user32.LockWorkStation():
        raise OSError('Windows could not lock this workstation')


def activation_environment(source=None):
    """Isolate Windows activation from large/custom music-shell environments.

    Windows PowerShell's CodeDOM compiler rejects an inherited environment over
    65535 bytes. The real V515 player had 142043 bytes. Do not copy unrelated
    player/shell variables or mutate the parent environment to work around it.
    """
    source = {key.upper(): value for key, value in (os.environ if source is None else source).items()}
    allowed = ('SYSTEMROOT', 'WINDIR', 'SYSTEMDRIVE', 'USERPROFILE', 'APPDATA',
               'LOCALAPPDATA', 'PROGRAMDATA', 'ALLUSERSPROFILE', 'TEMP', 'TMP',
               'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PROGRAMW6432',
               'COMMONPROGRAMFILES', 'COMMONPROGRAMFILES(X86)', 'COMMONPROGRAMW6432',
               'USERNAME', 'USERDOMAIN', 'USERDOMAIN_ROAMINGPROFILE', 'LOGONSERVER',
               'HOMEDRIVE', 'HOMEPATH', 'OS', 'PROCESSOR_ARCHITECTURE',
               'PROCESSOR_IDENTIFIER', 'PROCESSOR_LEVEL', 'PROCESSOR_REVISION',
               'NUMBER_OF_PROCESSORS', 'SESSIONNAME')
    result = {key: source[key] for key in allowed if source.get(key)}
    windows = Path(source.get('SYSTEMROOT') or source.get('WINDIR') or 'C:/Windows')
    result['SYSTEMROOT'] = result['WINDIR'] = str(windows)
    result['COMSPEC'] = str(windows / 'System32/cmd.exe')
    result['PATH'] = ';'.join(str(windows / part) for part in ('System32', '', 'System32/WindowsPowerShell/v1.0'))
    result['PSModulePath'] = str(windows / 'System32/WindowsPowerShell/v1.0/Modules')
    return result


class ManagedProcess:
    """Handles to our own publisher and a cooperative stop event, never audio."""
    def __init__(self):
        from ctypes import wintypes
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
        self.kernel.CreateEventW.restype = wintypes.HANDLE
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.SetEvent.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.lease = uuid.uuid4().hex
        self.event = self.kernel.CreateEventW(None, True, False, 'Local\\PAFPlayerManaged-' + self.lease)
        self.handle = None
        if not self.event:
            raise ctypes.WinError(ctypes.get_last_error())

    def attach(self, pid):
        self.pid = pid
        self.handle = self.kernel.OpenProcess(0x100000 | 0x1000, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        return self

    def poll(self):
        from ctypes import wintypes
        state = self.kernel.WaitForSingleObject(self.handle, 0)
        if state == 258:
            return None
        code = wintypes.DWORD()
        if state != 0 or not self.kernel.GetExitCodeProcess(self.handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value

    def wait(self, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            result = self.poll()
            if result is not None:
                return result
            time.sleep(.1)
        raise TimeoutError('Publisher did not exit')

    def signal(self):
        if self.event:
            self.kernel.SetEvent(self.event)

    def close(self):
        self.signal()
        for name in ('event', 'handle'):
            value = getattr(self, name)
            if value:
                self.kernel.CloseHandle(value)
                setattr(self, name, None)


def previous_setting():
    """Migrate an explicit companion choice, never enable a fresh installation."""
    local = os.environ.get('LOCALAPPDATA')
    if not local:
        return False
    for family in (FAMILY, 'ClaireCJS.PAFPlayer.LockScreen_vz06efybxc4j2'):
        path = Path(local) / 'Packages' / family / 'LocalState/publisher-settings.json'
        try:
            if path.stat().st_size > 16384:
                return False
            return json.loads(path.read_text(encoding='utf-8-sig')).get(KEY) is True
        except FileNotFoundError:
            continue
        except (OSError, ValueError, AttributeError):
            return False
    return False


def launch(server, identity):
    if os.name != 'nt':
        raise OSError('Windows 10 is required for lock-screen status')
    # Discover only our installed, signed package. Never execute a PATH match,
    # downloaded file, unverified external runtime, or the obsolete identity.
    script = r'''$ErrorActionPreference='Stop'
$env:PSModulePath=$env:WINDIR+'\System32\WindowsPowerShell\v1.0\Modules'
$p=Get-AppxPackage -Name ClaireCJS.PAFPlayer.LockScreen.Recovery
if (!$p -or $p.PackageFamilyName -ne 'ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2' -or [version]$p.Version -lt [version]'515.0.0.1') { throw 'Install PAFPlayer Lock Screen V515 or newer first' }
$exe=Join-Path $p.InstallLocation 'PAFPlayerLockScreen.exe'
$sig=Get-AuthenticodeSignature -LiteralPath $exe
if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Thumbprint -ne '08AC642F1C17B503BC857189AE8C78E76B3358EC') { throw 'Installed publisher signature does not match PAFPlayer' }
'''
    powershell = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0)
    child = ManagedProcess()
    arguments = subprocess.list2cmdline(['--managed', server, identity, str(os.getpid()), child.lease])
    # Packaged activation is required on this Windows installation; direct
    # CreateProcess on WindowsApps was rejected with ERROR_ACCESS_DENIED.
    script += r'''
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
[ComImport,Guid("2e941141-7f97-4756-ba1d-9decde894a3d"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IActivation { [PreserveSig] int ActivateApplication([MarshalAs(UnmanagedType.LPWStr)] string app, [MarshalAs(UnmanagedType.LPWStr)] string args, uint options, out uint pid); }
public static class Launch { public static uint Run(string args) {
var manager=(IActivation)Activator.CreateInstance(Type.GetTypeFromCLSID(new Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C")));
uint pid; int hr=manager.ActivateApplication("ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2!App",args,0,out pid);
if(hr<0) Marshal.ThrowExceptionForHR(hr); return pid; } }
'@
[Launch]::Run(''' + "'" + arguments.replace("'", "''") + "')"
    script = ("[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false); "
              "$ProgressPreference='SilentlyContinue'; try { " + script +
              " } catch { [Console]::Error.WriteLine($_.Exception.GetBaseException().Message); exit 1 }")
    try:
        result = subprocess.run([str(powershell), '-NoProfile', '-NonInteractive', '-EncodedCommand',
                                 base64.b64encode(script.encode('utf-16-le')).decode('ascii')],
                                capture_output=True, text=True, encoding='utf-8-sig', errors='replace',
                                timeout=20, creationflags=flags, env=activation_environment())
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            raise OSError('Lock-screen launch failed: ' + (detail[:210] or 'Windows PowerShell exit %s' % result.returncode))
        return child.attach(int(result.stdout.strip().splitlines()[-1]))
    except Exception:
        child.close()
        raise


class Controller:
    def __init__(self, owner, launcher=launch):
        self.owner, self.runtime, self.launcher = owner, owner.workflows, launcher
        self.process = None
        self.thread = None
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.next_attempt = 0.0
        self.message = 'Disabled'
        self.migrated = False
        self.install_busy = False
        self.install_message = ''
        self._install_checked_at = 0.0
        self._installed_version = ''

    def enabled(self):
        return self.runtime.settings.get(KEY) is True

    def start(self):
        if self.thread is not None:
            return
        self.thread = threading.Thread(target=self._run, name='paf-lock-screen', daemon=True)
        self.thread.start()

    def _release(self):
        if self.process is not None:
            # A named event stops our child. Its owner-process handle also
            # causes cleanup after a Python crash, without polling the player.
            try:
                self.process.close()
            except (OSError, AttributeError):
                pass
            self.process = None

    def _step(self):
        instance = getattr(self.runtime, 'instance', None)
        official = bool(instance and instance.owns())
        if not self.migrated:
            if official and KEY not in self.runtime.settings:
                with self.runtime.lock:
                    self.runtime.settings.setdefault(KEY, previous_setting())
                    self.runtime.save_settings()
            # Existing enabled lock-screen users asked to see the release during
            # the V530 rollout. Fresh/default profiles remain opted out.
            if official and self.runtime.settings.get(KEY) is True and VERSION_KEY not in self.runtime.settings:
                with self.runtime.lock:
                    self.runtime.settings[VERSION_KEY] = True
                    self.runtime.save_settings()
            self.migrated = official
        if self.stop.is_set() or not self.enabled() or not official:
            self._release()
            self.message = 'Disabled' if not self.enabled() else 'Waiting for official player ownership'
            return
        if self.process is not None:
            code = self.process.poll()
            if code is None:
                self.message = 'Publisher running; Windows controls lock-screen display'
                return
            self._release()
            self.message = 'Publisher exited (code %s); retrying in 30 seconds' % code
            self.next_attempt = time.monotonic() + 30
        if time.monotonic() < self.next_attempt:
            return
        self.next_attempt = time.monotonic() + 30
        server = 'http://127.0.0.1:%d' % self.owner.port
        self.process = self.launcher(server, instance.identity)
        self.message = 'Starting publisher'

    def _run(self):
        try:
            while not self.stop.is_set():
                try:
                    self._step()
                except Exception as error:
                    self.message = str(error)[:240]
                self.wake.wait(5)
                self.wake.clear()
        finally:
            self._release()

    def configure(self, payload):
        allowed = {'enabled': KEY, 'show_version': VERSION_KEY}
        if not payload or not set(payload).issubset(allowed) or any(type(value) is not bool for value in payload.values()):
            raise ValueError('Expected enabled/show_version checkbox values')
        with self.runtime.lock:
            old = dict(self.runtime.settings)
            for name, value in payload.items():
                self.runtime.settings[allowed[name]] = value
            try:
                self.runtime.save_settings()
            except Exception:
                self.runtime.settings.clear(); self.runtime.settings.update(old)
                raise
        self.next_attempt = 0
        self.wake.set()

    def refresh_installation(self, force=False):
        now = time.monotonic()
        if force or now - self._install_checked_at >= 10:
            self._installed_version = installed_version()
            self._install_checked_at = now
        return self._installed_version

    def install_async(self):
        if self.install_busy:
            return
        if uac_enabled() is False:
            raise OSError('UAC is disabled. Turn UAC on, reboot Windows, then return here and install the lock-screen integration.')
        self.install_busy = True
        self.install_message = 'Windows may show a UAC prompt. Approve it to install the lock-screen integration.'
        def worker():
            try:
                code = install_embedded_lockscreen(ask=lambda _prompt: 'yes')
                self.install_message = ('Lock-screen integration installed.' if code == 0
                                        else 'Installation did not complete. Approve the Windows UAC prompt and try again.')
            except Exception as error:
                self.install_message = str(error)[:240]
            finally:
                self.install_busy = False
                self.refresh_installation(True)
        threading.Thread(target=worker, name='paf-lock-screen-install', daemon=True).start()

    def perform(self, operation):
        if operation == 'test':
            lock_workstation(); return
        if operation == 'install':
            self.install_async(); return
        raise ValueError('Unknown lock-screen operation')

    def snapshot(self):
        version = self.refresh_installation()
        policy = uac_enabled()
        return {'enabled': self.enabled(), 'show_version': self.runtime.settings.get(VERSION_KEY) is True,
                'status': self.message, 'installed': version == EMBEDDED_INSTALL_VERSION,
                'installed_version': version, 'required_version': EMBEDDED_INSTALL_VERSION,
                'install_busy': self.install_busy, 'install_message': self.install_message,
                'uac_enabled': policy}

    def close(self):
        self.stop.set()
        self.wake.set()


def controller(owner):
    with owner.workflows.lock:
        if not hasattr(owner, '_lock_screen_controller'):
            owner._lock_screen_controller = Controller(owner)
        return owner._lock_screen_controller


def previous_lyric(timeline, position, offset, current):
    """Find the preceding nonblank cue without copying/transmitting the timeline."""
    if not current or not isinstance(timeline, (list, tuple)):
        return ''
    try:
        at = float(position) + float(offset)
        index = bisect_right(timeline, at, key=lambda cue: cue[0]) - 1
        # Bound work even for an unexpected run of empty cues. Normal compiled
        # timelines already collapse duplicate text and adjacent empty entries.
        for previous in range(index - 1, max(-1, index - 17), -1):
            text = str(timeline[previous][1] or '').strip()
            if text:
                return text
    except (TypeError, ValueError, IndexError):
        pass
    return ''


LOCKSCREEN_LYRIC_LEAD_SECONDS = 0.250


def lockscreen_lyric_context(timeline, position, offset, current, *, playing, paused, stopped, speed=1.0):
    """Advance only lock-screen text by 250 ms of playback, never a paused clock."""
    if stopped:
        return '', ''
    at = position
    if playing and not paused and isinstance(timeline, (list, tuple)) and timeline:
        try:
            rate = float(speed)
            if not math.isfinite(rate) or rate <= 0:
                rate = 1.0
            at = float(position) + LOCKSCREEN_LYRIC_LEAD_SECONDS * rate
            cue_time = at + float(offset)
            if not math.isfinite(cue_time):
                raise ValueError('Invalid lyric position')
            index = bisect_right(timeline, cue_time, key=lambda cue: cue[0]) - 1
            current = str(timeline[index][1] or '').strip() if index >= 0 else ''
        except (TypeError, ValueError, IndexError):
            at = position
    return current or '', previous_lyric(timeline, at, offset, current)


def handle(handler, owner, path):
    if path == '/api/remote-tray/hello' and parse_qs(urlsplit(handler.path).query).get('lockscreen') == ['1']:
        # Old players ignore this query and return the compatible hello envelope.
        if not ipaddress.ip_address(handler.client_address[0]).is_loopback:
            handler._json(403, {'error': 'Lock-screen status is local only'})
            return True
        if handler.command not in ('GET', 'HEAD'):
            handler.close_connection = True
            handler._json(405, {'error': 'Lock-screen status is read only'})
            return True
        instance = getattr(owner.workflows, 'instance', None)
        official = bool(instance and instance.owns())
        app = owner.workflows.app
        state = {}
        if official:
            # Keep the existing status/lyric cadence active without computing
            # browser spectrum frames. Copy no artwork or lyric timeline.
            owner.note_screensaver_activity()
            with owner._lock:
                raw = owner._state
                state = {key: raw[key] for key in
                         ('program', 'version', 'playing', 'paused', 'transport_stopped', 'lyric',
                          'position_seconds', 'duration_seconds')
                         if key in raw}
                tags, track = raw.get('metadata') or {}, raw.get('track') or {}
                state['metadata'] = {key: tags.get(key, '') for key in (
                    'Artist', 'artist', 'Song', 'title', 'Album', 'album',
                    'Year', 'year', 'Date', 'date',
                )}
                state['track'] = {'filename': track.get('filename', '')}
                state['lockscreen_show_version'] = owner.workflows.settings.get(VERSION_KEY) is True
                timeline = raw.get('lyric_timeline')
                position = raw.get('lyric_position_seconds', 0)
                offset = raw.get('karaoke_offset_seconds', 0)
                speed = raw.get('speed', 1.0)
            state['lyric'], state['lyric_previous'] = lockscreen_lyric_context(
                timeline, position, offset, state.get('lyric'),
                playing=state.get('playing', False), paused=state.get('paused', False),
                stopped=state.get('transport_stopped', False), speed=speed)
        handler._json(200, {'program': app.PROGRAM_TITLE, 'version': app.PROGRAM_VERSION,
                            'official': official, 'identity': instance.identity if official else '',
                            'state': state})
        return True
    if path != '/api/lockscreen/settings':
        return False
    try:
        if not ipaddress.ip_address(handler.client_address[0]).is_loopback:
            raise PermissionError('Lock-screen settings are local only')
        control = controller(owner)
        if handler.command == 'POST':
            length = int(handler.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024:
                handler.close_connection = True
                raise ValueError('Invalid request size')
            handler.connection.settimeout(2)
            body = handler.rfile.read(length)
            # Consume the bounded body before rejecting a token, so a persistent
            # browser connection cannot interpret it as the next HTTP request.
            from PAFPlayer_web_workflows import authorized
            authorized(handler, owner, owner.workflows, mutating=True)
            payload = json.loads(body.decode('utf-8'))
            if not isinstance(payload, dict):
                raise ValueError('Expected settings object')
            operation = payload.pop('operation', None)
            if operation is not None:
                if payload: raise ValueError('Operation requests cannot include settings')
                control.perform(str(operation))
            else:
                control.configure(payload)
        elif handler.command not in ('GET', 'HEAD'):
            raise ValueError('Unsupported method')
        handler._json(200, control.snapshot())
    except PermissionError as error:
        handler._json(403, {'error': str(error)})
    except (ValueError, OSError) as error:
        handler._json(400, {'error': str(error)})
    return True


HTML = '''<div class="group" id="lockScreenSection"><h3>Windows Lock Screen</h3>
<label><input type="checkbox" id="lockScreenEnabled" disabled>Enable lock-screen song status</label>
<label><input type="checkbox" id="lockScreenShowVersion" disabled>Show PAFPlayer version after album</label>
<div class="buttons"><button type="button" id="lockScreenTest" class="secondary-button">🔒 Test Lock Screen Now</button><button type="button" id="lockScreenInstall" class="secondary-button">🪟 Install / repair integration</button></div>
<p>PAFPlayer starts and stops its installed publisher automatically. In Windows Lock screen Settings, select PAFPlayer Lock Screen V530 for detailed status (song and clock, sung lyric, and album/year/version) and quick status (playing/paused badge).</p>
<p id="lockScreenInstallStatus" role="status">Checking installation…</p>
<p id="lockScreenStatus" role="status">Loading…</p></div>'''
SCRIPT = '''<script>(()=>{const box=document.getElementById('lockScreenEnabled'),version=document.getElementById('lockScreenShowVersion'),status=document.getElementById('lockScreenStatus'),installStatus=document.getElementById('lockScreenInstallStatus'),test=document.getElementById('lockScreenTest'),install=document.getElementById('lockScreenInstall');let busy=false;
async function refresh(){if(busy)return;try{const r=await fetch('/api/lockscreen/settings',{cache:'no-store'}),v=await r.json();if(!r.ok)throw Error(v.error);box.checked=v.enabled;version.checked=v.show_version;box.disabled=version.disabled=false;install.disabled=!!v.install_busy;install.textContent=v.install_busy?'Installing…':'🪟 Install / repair integration';installStatus.textContent=v.installed?'Integration installed (v'+v.installed_version+').':(v.uac_enabled===false?'Integration is not installed. UAC is disabled: turn UAC on, reboot Windows, then install it here.':'Integration is not installed. Use Install / repair integration; approve the Windows UAC prompt if shown.')+(v.install_message?' '+v.install_message:'');status.textContent=v.status}catch(e){status.textContent=String(e)}}
async function save(payload){busy=true;box.disabled=version.disabled=true;try{const r=await fetch('/api/workflows/status'),a=await r.json();if(!r.ok||!a.local||!a.token)throw Error('Use the controls on the player computer');const s=await fetch('/api/lockscreen/settings',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':a.token},body:JSON.stringify(payload)}),v=await s.json();if(!s.ok)throw Error(v.error);box.checked=v.enabled;version.checked=v.show_version;status.textContent='Setting saved'}catch(e){status.textContent=String(e)}finally{busy=false;box.disabled=version.disabled=false}}
box.onchange=()=>save({enabled:box.checked});version.onchange=()=>save({show_version:version.checked});install.onclick=()=>save({operation:'install'});test.onclick=()=>{if(confirm('Lock this Windows workstation now to test the PAFPlayer lock-screen display?'))save({operation:'test'})};refresh();setInterval(()=>{if(!document.hidden)refresh()},5000)})();</script>'''


def augment(page):
    return page.replace('<div class="group" id="visualScreensaverSection">', HTML + '<div class="group" id="visualScreensaverSection">', 1).replace('</body>', SCRIPT + '</body>', 1)
