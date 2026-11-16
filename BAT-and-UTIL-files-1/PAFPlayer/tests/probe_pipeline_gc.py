"""Offline bounded allocation probe; never changes the running player or GC policy."""
import ast
from collections import Counter
from datetime import datetime
import gc
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import time
import types
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT/'PAFPlayer.py'
sys.path.insert(0, str(ROOT/'tests'))
from run_PAFPlayer_tests import install_guards, unique
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
stage = unique(ROOT/'tests/runs'/('pipeline-gc-'+stamp)); stage.mkdir()
with (stage/'PAFPlayer.py').open('xb') as f: f.write(source.read_bytes())
for key in ('APPDATA', 'LOCALAPPDATA', 'TMP', 'TEMP'): os.environ[key] = str(stage)
tempfile.tempdir = str(stage)
os.environ['PLAY_AUDIO_FILE_HISTORY_DB'] = str(stage/'history.sqlite3')
sys.path.insert(0, str(stage)); sys.argv = ['PAFPlayer.py', '--unit-tests']; os.chdir(stage)
blocked = install_guards(ROOT/'tests')
import PAFPlayer as app

results = []
def probe(name, function, count=100):
    # DEBUG_SAVEALL/disabled automatic GC apply only inside this test process,
    # for this bounded batch. Restore policy before proceeding to another case.
    for _ in range(3): function()
    gc.collect(); old_debug = gc.get_debug(); enabled = gc.isenabled()
    gc.disable(); gc.set_debug(gc.DEBUG_SAVEALL)
    pointer_before = len(app.ctypes._pointer_type_cache)
    function_before = len(app.ctypes._win_functype_cache)
    before = gc.get_count(); begin = time.perf_counter()
    try:
        for _ in range(count): function()
        elapsed = time.perf_counter() - begin
        growth = tuple(a-b for a,b in zip(gc.get_count(), before))
        collected = gc.collect()
        kinds = Counter(type(o).__module__+'.'+type(o).__qualname__ for o in gc.garbage)
        functions = Counter(o.__qualname__ for o in gc.garbage if isinstance(o, types.FunctionType))
        classes = Counter(o.__qualname__ for o in gc.garbage if isinstance(o, type))
        entry = dict(name=name, calls=count, ms_per_call=elapsed*1000/count,
                     tracked_growth=growth, unreachable=collected,
                     retained_pointer_types=len(app.ctypes._pointer_type_cache)-pointer_before,
                     retained_function_types=len(app.ctypes._win_functype_cache)-function_before,
                     types=kinds.most_common(15), functions=functions.most_common(20),
                     classes=classes.most_common(20))
        results.append(entry); print(json.dumps(entry), flush=True)
    finally:
        gc.set_debug(old_debug); gc.garbage.clear(); gc.collect()
        if enabled: gc.enable()

probe('noop', lambda: None)
probe('diagnostics', app.paf_runtime_diagnostics_snapshot)
probe('thread_stacks', app.paf_runtime_thread_stacks)
probe('idle_input', app.windows_last_input_tick)
probe('console_geometry', app.console_cursor_and_viewport_top)
probe('lock_state', app.windows_session_is_locked)
def probe_audio_thread():
    import threading
    worker = threading.Thread(target=lambda: probe('external_audio_sessions', app.probe_external_audio_sessions, 20))
    worker.start(); worker.join()
probe_audio_thread()
import PAFPlayer_steam
probe('steam_process_images', PAFPlayer_steam.process_images, 20)
with mock.patch.object(app.ctypes.windll, 'kernel32', types.SimpleNamespace(
        GetStdHandle=lambda n: 1, GetConsoleCursorInfo=lambda *a: True,
        SetConsoleCursorInfo=lambda *a: True)):
    probe('cursor_visibility', lambda: app.set_console_cursor_visible(False))

rng = random.Random(651); width = 140; rows = 48
grid = tuple(tuple(tuple(rng.randrange(256) for _ in range(3)) for _ in range(width*2)) for _ in range(rows))
micro = tuple(tuple(tuple(rng.randrange(256) for _ in range(3)) for _ in range(width*2)) for _ in range(rows*4))
app.ARTWORK_SEAM_STRATEGY = 5
heights = [rng.random() for _ in range(width*2)]
render_args = dict(columns=width, spectrum_levels=bytes(range(256)), recent_energy=heights,
    height_override=heights, granularity=3, rows=rows, truncate_top_lines=0,
    processing_style=62, artwork_color_grid=grid, artwork_microtile_color_grid=micro,
    artwork_bar_strength=1, artwork_bar_blend_mode=1, artwork_bar_opacity=.5,
    artwork_background_strength=.1, artwork_microtiles_enabled=True,
    artwork_bar_microtiles_enabled=True, artwork_microtile_detail_mode=9,
    artwork_bar_microtile_detail_mode=9, semantic_cells_only=True)
def render():
    cells = []; app.render_drcs_visualizer(**render_args, cell_rows_out=cells)
    return cells
probe('render_artwork', render)
probe('render_bare', lambda: app.render_drcs_visualizer(width, bytes(range(256)), heights,
    height_override=heights, granularity=3, rows=rows, processing_style=62,
    cell_rows_out=[], semantic_cells_only=True))

report = unique(ROOT/'tests/reports'/('pipeline-gc-'+app.PROGRAM_VERSION+'-'+stamp+'.json'))
with report.open('x', encoding='utf8') as f:
    json.dump(dict(version=app.PROGRAM_VERSION, source_sha256=hashlib.sha256((stage/'PAFPlayer.py').read_bytes()).hexdigest(),
        native_composer=app._visualizer_luma_composer() is not None, results=results,
        blocked_writes=blocked, stage=str(stage)), f, indent=2)
print(report)
