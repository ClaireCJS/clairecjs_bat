r"""PAFPlayer installed-source bridge and explicitly marked internal COPY fallback.

Original fallback: C:\BAT\PAFPlayer\PAFPlayer.py, PROGRAM_VERSION V567,
copied 2026-10-27. SHA-256: 9ddb9ba5f0dce14303d6c209cb03ba0c5e1b8aed796e71852b4e9c98baf644a1
These terminal routines are verbatim copies with their original names/ranges.
The bridge prefers the current sibling ../PAFPlayer/PAFPlayer.py at runtime.
Only the named artwork functions are compiled; the player is never imported,
initialized, started, or given any image as an audio/playback target.
"""
from __future__ import annotations
import ast
from functools import lru_cache
import hashlib
import io
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from types import SimpleNamespace,FunctionType

from .errors import DependencyUnavailable

# COPIED FROM PAFPlayer: terminal_cell_pixel_size_nonintrusive, original lines 19328-19377.
def terminal_cell_pixel_size_nonintrusive(*, use_win32_font: bool = True) -> tuple[int, int]:
    """Return terminal character-cell pixels without issuing VT window queries.

    Earlier builds repeatedly called claire_terminal_geometry.query_terminal_geometry(),
    which sends CSI 14t/16t/18t terminal-window queries and temporarily changes console
    input mode.  That is clever, but on some Windows Terminal/ConPTY configurations it
    can disturb another application's fullscreen/focus state.  The player only needs an
    approximate font-cell ratio for SIXEL sizing, so V27 uses the passive Win32 font API
    (or a conservative fallback) and never sends terminal-window-control queries during
    playback.
    """
    now = time.monotonic()
    cached = getattr(terminal_cell_pixel_size_nonintrusive, "_cached", None)
    cached_at = getattr(terminal_cell_pixel_size_nonintrusive, "_cached_at", -60.0)
    if cached is not None and now - cached_at < 30.0:
        return cached
    result = (10, 20)
    if os.name == "nt" and use_win32_font:
        try:
            import ctypes
            from ctypes import wintypes

            class COORD(ctypes.Structure):
                _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

            class CONSOLE_FONT_INFOEX(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.ULONG),
                    ("nFont", wintypes.DWORD),
                    ("dwFontSize", COORD),
                    ("FontFamily", wintypes.UINT),
                    ("FontWeight", wintypes.UINT),
                    ("FaceName", wintypes.WCHAR * 32),
                ]

            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            info = CONSOLE_FONT_INFOEX()
            info.cbSize = ctypes.sizeof(info)
            if ctypes.windll.kernel32.GetCurrentConsoleFontEx(
                handle, False, ctypes.byref(info)
            ):
                width = int(info.dwFontSize.X)
                height = int(info.dwFontSize.Y)
                if width > 0 and height > 0:
                    result = (width, height)
        except (AttributeError, OSError, TypeError, ValueError):
            pass
    terminal_cell_pixel_size_nonintrusive._cached = result
    terminal_cell_pixel_size_nonintrusive._cached_at = now
    return result

# COPIED FROM PAFPlayer: render_sixel_album_art_layer, original lines 50554-50593.
def render_sixel_album_art_layer(
    audio_path: Path,
    columns: int,
    rows: int,
) -> bytes:
    """Return a cached, static SIXEL cover layer for the V196 overlay experiment."""
    rows = max(1, int(rows))
    columns = max(1, int(columns))
    cache = getattr(render_sixel_album_art_layer, "_cache", {})
    key = (str(Path(audio_path).resolve()), columns, rows)
    if key in cache:
        return cache[key]
    chafa = shutil.which("chafa")
    art = extract_album_art(audio_path)
    if not chafa or not art:
        return b""
    cell_width, cell_height = terminal_cell_pixel_size_nonintrusive()
    view_width = max(1, math.ceil(columns * cell_width / 8))
    view_height = max(1, math.ceil(rows * cell_height / 8))
    try:
        payload = subprocess.run(
            [
                chafa, "--format=sixels", "--colors=64", "--scale=max",
                f"--size={columns}x{rows}",
                f"--view-size={view_width}x{view_height}",
                f"--font-ratio={cell_width}/{cell_height}",
                "--optimize=9", "--work=9", "--color-space=din99d", "-",
            ],
            input=art,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=4,
        ).stdout
        payload = payload.replace(b"\033[?25l", b"").replace(b"\033[?25h", b"")
        # Only the current layout is useful; bound retained cover data tightly.
        render_sixel_album_art_layer._cache = {key: payload}
        return payload
    except (OSError, subprocess.TimeoutExpired):
        return b""


GUI_NAMES=('external_album_art_monitor_work_areas','_parse_external_album_art_geometry',
           'clamp_external_album_art_geometry','_pillow_fit_canvas_image','reuse_or_create_photoimage')
TERMINAL_NAMES=('terminal_cell_pixel_size_nonintrusive','render_sixel_album_art_layer')


def image_bytes(path):
    """Normalize orientation in memory; neither preview mode changes the file."""
    from PIL import Image,ImageOps
    with Image.open(path) as opened:
        image=ImageOps.exif_transpose(opened).convert('RGBA')
    output=io.BytesIO();image.save(output,format='PNG')
    return output.getvalue()


def _namespace(root):
    private=Path(root)/'environment/tools/chafa/chafa.exe'
    def which(name):
        return str(private) if name=='chafa' and private.is_file() else shutil.which(name)
    def run(command,*args,**options):
        # PAFPlayer's V567 layer requests 64 colors, but the bundled Chafa
        # 1.18.2 CLI rejects that palette value. Keep the installed routine
        # itself untouched and adapt only its process arguments to full color.
        command=['--colors=full' if value=='--colors=64' else value for value in command]
        return subprocess.run(command,*args,**options)
    return {'__name__':'icgf_paf_artwork_routines','io':io,'os':os,'re':re,'Path':Path,
            'math':math,'time':time,'shutil':SimpleNamespace(which=which),
            'subprocess':SimpleNamespace(run=run,PIPE=subprocess.PIPE,DEVNULL=subprocess.DEVNULL,TimeoutExpired=subprocess.TimeoutExpired),
            'extract_album_art':image_bytes,'EXTERNAL_ALBUM_ART_MIN_SIZE':160,
            'EXTERNAL_ALBUM_ART_DEFAULT_SIZE':520}


def _monitor_adapter(function):
    def monitors():
        if os.name=='nt':
            import ctypes
            from ctypes import wintypes
            user32=ctypes.windll.user32
            # Preserve the installed PAF function, with pointer-safe signatures
            # independent of which local MONITORINFO structure it defines.
            user32.GetMonitorInfoW.argtypes=[wintypes.HANDLE,ctypes.c_void_p]
            user32.GetMonitorInfoW.restype=wintypes.BOOL
            user32.EnumDisplayMonitors.argtypes=[wintypes.HDC,ctypes.c_void_p,ctypes.c_void_p,wintypes.LPARAM]
            user32.EnumDisplayMonitors.restype=wintypes.BOOL
        return function()
    return monitors


@lru_cache(maxsize=4)
def _load(root_text,source_text,size,mtime_ns):
    from . import paf_album_art as internal
    namespace=_namespace(root_text);reason=None;digest=None;version=None
    source=Path(source_text)
    installed=False
    if size>=0:
        try:
            data=source.read_bytes();tree=ast.parse(data.decode('utf-8-sig'),filename=str(source))
            wanted=set(GUI_NAMES+TERMINAL_NAMES)
            functions={node.name:node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name in wanted}
            if set(functions)!=wanted: raise ValueError('Required artwork routines are absent')
            for node in tree.body:
                if isinstance(node,ast.Assign):
                    for target in node.targets:
                        if isinstance(target,ast.Name) and target.id in ('EXTERNAL_ALBUM_ART_MIN_SIZE','EXTERNAL_ALBUM_ART_DEFAULT_SIZE','PROGRAM_VERSION'):
                            value=ast.literal_eval(node.value)
                            if target.id=='PROGRAM_VERSION': version=str(value)
                            else: namespace[target.id]=int(value)
            module=ast.Module(body=[functions[name] for name in GUI_NAMES+TERMINAL_NAMES],type_ignores=[])
            # No top-level imports, assignments, hooks, GUI startup, or main()
            # from PAFPlayer are executed. Only these artwork definitions load.
            exec(compile(module,str(source),'exec',dont_inherit=False),namespace)
            digest=hashlib.sha256(data).hexdigest();installed=True
        except (OSError,ValueError,SyntaxError,TypeError,NameError) as error:
            reason='Installed PAFPlayer artwork routines could not load: '+type(error).__name__
    else: reason='Sibling ../PAFPlayer/PAFPlayer.py was not found'
    if not installed:
        for name in GUI_NAMES: namespace[name]=getattr(internal,name)
        for name in TERMINAL_NAMES:
            copied=globals()[name]
            function=FunctionType(copied.__code__,namespace,name,copied.__defaults__)
            function.__kwdefaults__=copied.__kwdefaults__
            namespace[name]=function
    return SimpleNamespace(
        origin='installed-pafplayer' if installed else 'internal-pafplayer-copy',
        source=str(source) if installed else str(Path(internal.__file__)),
        source_sha256=digest,version=version,fallback_reason=reason,
        monitors=_monitor_adapter(namespace['external_album_art_monitor_work_areas']),
        clamp=namespace['clamp_external_album_art_geometry'],
        fit=namespace['_pillow_fit_canvas_image'],photo=namespace['reuse_or_create_photoimage'],
        terminal=namespace['render_sixel_album_art_layer'])


def get_backend(root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parents[2]
    root=root.resolve();source=root.parent/'PAFPlayer/PAFPlayer.py'
    try: state=source.stat();size=state.st_size;mtime=state.st_mtime_ns
    except OSError: size=-1;mtime=-1
    return _load(str(root),str(source),size,mtime)


def status(root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parents[2]
    backend=get_backend(root)
    from .paf_drcs import status as drcs_status
    return {'origin':backend.origin,'source':backend.source,'source_sha256':backend.source_sha256,
            'pafplayer_version':backend.version,'fallback_reason':backend.fallback_reason,
            'terminal':drcs_status(root)}


def terminal_image(root,path,columns,rows):
    from .paf_drcs import render
    return render(root,path,columns,rows)

