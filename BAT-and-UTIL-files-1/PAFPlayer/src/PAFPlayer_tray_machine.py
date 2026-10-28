"""Per-Windows-user tray presentation, independent of the playback server."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path
import threading
import time


REGISTRY_PATH = r'Software\ClaireCJS\PAFPlayer\TrayMachine'
OPTION_VALUES = {'lyrics_tooltip': 'LyricsTooltip', 'album_wallpaper': 'AlbumWallpaper',
                 'remote_hotkeys': 'RemoteHotkeys', 'remote_floating_lyrics': 'RemoteFloatingLyrics',
                 'remote_album_art': 'RemoteAlbumArt'}
OPTION_DEFAULTS = {name: name == 'remote_hotkeys' for name in OPTION_VALUES}
SPI_GETDESKWALLPAPER = 0x0073
SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATEINIFILE = 0x0001
SPIF_SENDCHANGE = 0x0002


class MachineSettings:
    """HKCU values on this computer; never sent to or saved by the server."""
    def options(self):
        values = dict(OPTION_DEFAULTS)
        if os.name != 'nt':
            return values
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
                for name, value_name in OPTION_VALUES.items():
                    try:
                        value, _kind = winreg.QueryValueEx(key, value_name)
                        values[name] = bool(int(value))
                    except (OSError, TypeError, ValueError):
                        pass
        except OSError:
            pass
        return values

    def set_option(self, name, enabled):
        if name not in OPTION_VALUES or type(enabled) is not bool:
            raise ValueError('Unknown tray machine option')
        if os.name == 'nt':
            import winreg
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
                winreg.SetValueEx(key, OPTION_VALUES[name], 0, winreg.REG_DWORD, int(enabled))

    def wallpaper_lease(self):
        if os.name != 'nt':
            return '', ''
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
                original = winreg.QueryValueEx(key, 'WallpaperOriginal')[0]
                applied = winreg.QueryValueEx(key, 'WallpaperApplied')[0]
                return str(original), str(applied)
        except OSError:
            return '', ''

    def save_wallpaper_lease(self, original, applied):
        if os.name != 'nt':
            return
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
            winreg.SetValueEx(key, 'WallpaperOriginal', 0, winreg.REG_SZ, str(original))
            winreg.SetValueEx(key, 'WallpaperApplied', 0, winreg.REG_SZ, str(applied))


def current_wallpaper():
    buffer = ctypes.create_unicode_buffer(32768)
    system_parameters = ctypes.WinDLL('user32', use_last_error=True)['SystemParametersInfoW']
    system_parameters.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
    system_parameters.restype = wintypes.BOOL
    if not system_parameters(SPI_GETDESKWALLPAPER, len(buffer), buffer, 0):
        raise OSError(ctypes.get_last_error(), 'Could not read the desktop wallpaper')
    return buffer.value


def set_wallpaper(path):
    system_parameters = ctypes.WinDLL('user32', use_last_error=True)['SystemParametersInfoW']
    system_parameters.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
    system_parameters.restype = wintypes.BOOL
    if not system_parameters(SPI_SETDESKWALLPAPER, 0, str(path),
                                        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE):
        raise OSError(ctypes.get_last_error(), 'Could not set the desktop wallpaper')


def same_wallpaper(first, second):
    return os.path.normcase(os.path.abspath(str(first))) == os.path.normcase(os.path.abspath(str(second)))


def cache_bitmap(data, directory=None):
    """Content-addressed new file: never replace a wallpaper already in use."""
    root = Path(directory or (Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'PAFPlayer' / 'TrayWallpaper'))
    root.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()
    base = 'album-' + digest[:24]
    index = 0
    while True:
        filename = base + (f' ({index})' if index else '') + '.bmp'
        path = root / filename
        try:
            with path.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            return path
        except FileExistsError:
            try:
                if hashlib.sha256(path.read_bytes()).hexdigest() == digest:
                    return path
            except OSError:
                pass
            index += 1


def recycle_cached(path, directory=None):
    """Keep the file if safe recycling is unavailable."""
    if not path:
        return
    try:
        from send2trash import send2trash
        root = Path(directory or (Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'PAFPlayer' / 'TrayWallpaper'))
        candidate = Path(path)
        if (candidate.is_file() and candidate.parent.resolve() == root.resolve()
                and candidate.name.startswith('album-') and candidate.suffix == '.bmp'):
            send2trash(str(candidate))
    except (ImportError, OSError):
        pass


class TrayMachineEffects:
    def __init__(self, server, owner, refresh, *, remote=False, settings=None, cache_directory=None):
        self.server, self.owner, self.refresh = server, owner, refresh
        self.remote = remote
        self.settings = settings or MachineSettings()
        self.cache_directory = cache_directory
        self.options = self.settings.options()
        self.lyric = ''
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = None
        self._mutex = None
        self._last_key = None
        self._last_attempt = 0.0
        self._original, self._applied = self.settings.wallpaper_lease()
        self.last_error = ''

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name='paf-tray-machine', daemon=True)
        self._thread.start()

    def toggle(self, name):
        if name not in OPTION_VALUES:
            return False
        return self.set_option(name, not self.options[name])

    def set_option(self, name, value):
        """Set a machine choice without hiding an already-visible remote window."""
        if name not in OPTION_VALUES or type(value) is not bool:
            return False
        if self.options[name] == value:
            return True
        self.settings.set_option(name, value)
        self.options[name] = value
        self._wake.set()
        self.refresh()
        return True

    def tooltip_lyric(self):
        return self.lyric if self.options['lyrics_tooltip'] else ''

    def _connected(self):
        return bool(self.owner.owns() and (not self.remote or self.server.connected))

    def _key(self, state):
        track = state.get('track') or {}
        if (not self._connected() or not track.get('path') or not int(state.get('art_count') or 0)
                or not (state.get('playing') or state.get('paused'))):
            return None
        identity = getattr(self.server, 'owner_identity', '') if self.remote else getattr(self.owner, 'identity', '')
        return identity, str(track['path']), int(state.get('art_generation') or 0)

    def _claim_wallpaper(self):
        if self._mutex:
            return True
        kernel = ctypes.windll.kernel32
        kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        kernel.CreateMutexW.restype = wintypes.HANDLE
        kernel.GetLastError.restype = wintypes.DWORD
        handle = kernel.CreateMutexW(None, True, 'Local\\PAFPlayerTrayWallpaper')
        if not handle:
            raise OSError('Could not claim the desktop wallpaper')
        if kernel.GetLastError() == 183:
            kernel.CloseHandle(handle)
            return False
        self._mutex = handle
        return True

    def _release_wallpaper(self):
        if self._mutex:
            kernel = ctypes.windll.kernel32
            kernel.ReleaseMutex(self._mutex)
            kernel.CloseHandle(self._mutex)
            self._mutex = None

    def _bitmap(self, generation, width, height):
        if self.remote:
            return self.server.wallpaper(generation, width, height)
        from PAFPlayer_track_details import wallpaper_bitmap
        art, _mime = self.server.art_snapshot_at_generation(generation, 0)
        return wallpaper_bitmap(art, width, height) if art else None

    def _apply(self, key):
        if not self._claim_wallpaper():
            return False
        try:
            width = min(1920, max(320, ctypes.windll.user32.GetSystemMetrics(0)))
            height = min(1080, max(240, ctypes.windll.user32.GetSystemMetrics(1)))
            data = self._bitmap(key[2], width, height)
            if not data or self._stop.is_set() or self._key(self.server.snapshot()) != key:
                return False
            path = cache_bitmap(data, self.cache_directory)
            previous_applied = self._applied
            actual = current_wallpaper()
            if not previous_applied or not same_wallpaper(actual, previous_applied):
                self._original = actual
            set_wallpaper(path)
            self._applied = str(path)
            self.settings.save_wallpaper_lease(self._original, self._applied)
            self._last_key = key
            if previous_applied and not same_wallpaper(previous_applied, path):
                recycle_cached(previous_applied, self.cache_directory)
            return True
        finally:
            if not self._applied:
                self._release_wallpaper()

    def _restore(self):
        previous = self._applied
        if previous:
            try:
                if not self._claim_wallpaper():
                    return
                if same_wallpaper(current_wallpaper(), previous):
                    set_wallpaper(self._original)
                self.settings.save_wallpaper_lease('', '')
                self._applied = ''
                self._original = ''
                recycle_cached(previous, self.cache_directory)
            except OSError as exc:
                self.last_error = str(exc)
        self._last_key = None
        self._release_wallpaper()

    def step(self):
        state = self.server.snapshot() if self.server else {}
        if self.remote:
            self.server.poll_interval = (
                .4 if self.options['lyrics_tooltip']
                else 1.0 if (self.options.get('remote_floating_lyrics')
                             or self.options.get('remote_album_art'))
                else 2.0
            )
        lyric = (' '.join(str(state.get('lyric') or '').split())[:100]
                 if self._connected() and self.options['lyrics_tooltip'] else '')
        if lyric != self.lyric:
            self.lyric = lyric
            self.refresh()
        key = self._key(state) if self.options['album_wallpaper'] else None
        if key is None:
            if self._applied or self._mutex:
                self._restore()
            return
        if key != self._last_key and time.monotonic() - self._last_attempt >= 3:
            self._last_attempt = time.monotonic()
            try:
                if self._apply(key):
                    self.last_error = ''
                else:
                    self.last_error = 'Artwork is unavailable or another PAFPlayer tray owns this desktop'
                    if self._applied and self._last_key != key:
                        self._restore()
            except (OSError, ValueError) as exc:
                self.last_error = str(exc)
                if self._applied and self._last_key != key:
                    self._restore()

    def _run(self):
        last_reload = 0.0
        while not self._stop.is_set():
            if time.monotonic() - last_reload >= 2:
                try:
                    self.options = self.settings.options()
                except OSError:
                    pass
                last_reload = time.monotonic()
            try:
                self.step()
            except (OSError, ValueError) as exc:
                self.last_error = str(exc)
            self._wake.wait(.4)
            self._wake.clear()
        self._restore()

    def close(self):
        self._stop.set()
        self._wake.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=7)
        if not self._thread or not self._thread.is_alive():
            self._restore()
