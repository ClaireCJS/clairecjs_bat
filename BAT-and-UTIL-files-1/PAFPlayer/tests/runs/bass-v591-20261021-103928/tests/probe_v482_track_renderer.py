"""Exercise the real nested renderer without audio, threads, history or settings writes."""
import ast
import contextlib
import io
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import PAFPlayer as app

TRACK = Path(r"T:\new\MUSIC\changerrecent\Metalocalypse\MISC\Murdertrain A Comin' (TV Edit) [from S1E14_Bluesklok].mp3")


def capture_renderer(width=170, height=30):
    tree = ast.parse((ROOT / 'pafplayer.py').read_text(encoding='utf-8-sig'))
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'play_audio_file')
    # Return the initialized renderer closures BEFORE entering playback's try
    # block. Keep unreachable code for Python's closure-binding analysis.
    index = next(i for i, n in enumerate(func.body) if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'previous_cursor_hide_append_enabled' for t in n.targets))
    func.body.insert(index, ast.Return(value=ast.Call(func=ast.Name(id='locals', ctx=ast.Load()),args=[],keywords=[])))
    namespace = dict(vars(app))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[func],type_ignores=[])), '<renderer-only>', 'exec'), namespace)
    changes = dict(
        cache_playlist_history_identity=lambda *a, **k:None,
        playlist_history_last_played=lambda *a, **k:1.0,
        append_pafplayer_trace=lambda *a, **k:None,
        set_console_title=lambda *a, **k:None,
        get_console_title=lambda:'renderer test',
        audio_is_effectively_learned=lambda *a, **k:False,
        set_console_cursor_visible=lambda *a, **k:None,
    )
    namespace.update(changes)
    for name in tuple(namespace):
        if name.startswith(('save_', 'write_')) and callable(namespace[name]):
            namespace[name] = lambda *a, **k:None
    with mock.patch.object(app.threading.Thread, 'start', lambda self:None), \
         mock.patch.object(app.shutil, 'get_terminal_size', return_value=os.terminal_size((width,height))):
        local = namespace['play_audio_file'](
            TRACK, install_signal_handlers=False, manage_winamp=False, guard_winamp=False,
            external_media_controller=SimpleNamespace(pause_reason=''),
            duration_probe=lambda path:48.065306, trim_edge_silence=False,
            attribute_management_enabled=False, album_art_display=False,
            drcs_visualizer=True, sixel_visualizer=False, smooth_audio_renderer_enabled=False,
            mm_inspired_renderer_state=[False], visualizer_input_source_state=[0],
            visualizer_rows_state=[32], karaoke_visualizer_height_mode_state=[0],
            karaoke_emojimax_state=[False],
        )
    return local, namespace


def main():
    local, namespace = capture_renderer()
    show = local['show_status']
    cells = dict(zip(show.__code__.co_freevars, show.__closure__))
    missing = []
    for name, cell in cells.items():
        try: cell.cell_contents
        except ValueError: missing.append(name)
    print('uninitialized after preparation:', missing)
    print('geometry:', {k:local.get(k) for k in ('UI_ROWS','LYRIC_ROW','LYRIC_ROWS','DRCS_ROW','drcs_rows','STATUS_ROW')})
    output = []
    namespace['write_console'] = output.append
    cells['drcs_timeline'].cell_contents = (bytes([30]*12*40*50),12,40)
    for name in missing:
        cells[name].cell_contents = False
    with mock.patch.object(app.shutil, 'get_terminal_size', return_value=os.terminal_size((170,30))):
        for tick in range(25*30,33*30):
            now = tick/30
            show(now,'▶️')
    print('paints:', len(output), 'characters:', sum(map(len,output)), 'newlines:',sum(x.count('\n') for x in output))


def native_track():
    import ctypes
    import json
    import msvcrt
    from ctypes import wintypes
    kernel = app._windows_console_text_api()
    class Coord(ctypes.Structure):
        _fields_ = [('X',ctypes.c_short),('Y',ctypes.c_short)]
    class Rect(ctypes.Structure):
        _fields_ = [(name,ctypes.c_short) for name in ('Left','Top','Right','Bottom')]
    class Info(ctypes.Structure):
        _fields_ = [('size',Coord),('cursor',Coord),('attrs',wintypes.WORD),('window',Rect),('maximum',Coord)]
    kernel.GetConsoleScreenBufferInfo.argtypes = [wintypes.HANDLE,ctypes.POINTER(Info)]
    kernel.SetConsoleMode.argtypes = [wintypes.HANDLE,wintypes.DWORD]
    with open('CONOUT$', 'w', encoding='utf-8') as stream:
        handle = msvcrt.get_osfhandle(stream.fileno())
        info = Info()
        assert kernel.GetConsoleScreenBufferInfo(handle,ctypes.byref(info))
        width, height = info.size.X, info.window.Bottom-info.window.Top+1
        assert kernel.SetConsoleMode(handle, 7)
        local, namespace = capture_renderer(width,height)
        show = local['show_status']
        cells = dict(zip(show.__code__.co_freevars,show.__closure__))
        cells['drcs_timeline'].cell_contents = (bytes([30]*12*40*50),12,40)
        cells['spectrum_analysis_columns'].cell_contents = 12
        namespace['write_console'] = app.write_console
        max_top = 0
        with mock.patch.object(app.sys,'stdout',stream), \
             mock.patch.object(app.shutil,'get_terminal_size',return_value=os.terminal_size((width,height))):
            for tick in range(25*30,33*30):
                show(tick/30,'▶️')
                local['render_metadata_rows'](tick/30)
                assert kernel.GetConsoleScreenBufferInfo(handle,ctypes.byref(info))
                max_top = max(max_top,info.window.Top)
    print(json.dumps(dict(frames=240,max_viewport_top=max_top,width=width,height=height)))


if __name__ == '__main__':
    if '--native-track' in sys.argv: native_track()
    else: main()
