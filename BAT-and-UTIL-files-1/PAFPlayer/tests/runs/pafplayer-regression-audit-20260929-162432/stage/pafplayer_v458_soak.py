"""Accelerated retained-cover/title and moving-frame check, without live playback.

Usage: python -B pafplayer_v458_soak.py PAFPlayer.py result.json
Run old and candidate in separate processes. Reports distinguish cache churn
from renderer timing. This is not an hours-long real Tk/terminal soak.
"""
import gc
from types import SimpleNamespace
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import queue
import statistics
import sys
import threading
import time
from unittest import mock
import psutil

filename, output = sys.argv[1:3]
sys.argv = [filename, '--unit-tests']
process = psutil.Process()
process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
spec = importlib.util.spec_from_file_location('soak_player', filename)
app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app
spec.loader.exec_module(app)


def memory():
    info = process.memory_info()
    return {'private_mib': round(info.private / 2**20, 2), 'rss_mib': round(info.rss / 2**20, 2)}


report = {'source': str(Path(filename).resolve()), 'sha256': hashlib.sha256(Path(filename).read_bytes()).hexdigest(), 'initial': memory()}
report['artwork'] = []
with mock.patch.object(app, '_album_art_candidates', return_value=[]), mock.patch.object(app, '_folder_uses_per_track_sidecar_art', return_value=False), mock.patch.object(app, '_extract_tagged_embedded_cover_art', side_effect=lambda path: bytes([int(path.stem.split('-')[-1]) % 256]) * (1024 * 1024)), mock.patch.object(app, '_materialize_cover_sidecar_from_embedded_art', new=lambda path, art: None):
    for index in range(512):
        # A new 1-MiB payload for every synthetic track, exactly as a cache miss
        # returns independently read embedded/sidecar bytes in production.
        app.extract_album_art(Path(f'nonexistent-soak-track-{index}.flac'))
        if (index + 1) % 64 == 0:
            report['artwork'].append({'tracks': index + 1, 'entries': len(app._ALBUM_ART_BYTES_CACHE), 'payload_mib': sum(len(value or b'') for value in app._ALBUM_ART_BYTES_CACHE.values()) / 2**20, **memory()})
print(json.dumps({'artwork':report['artwork']}), flush=True)

window = app.ExternalAlbumArtWindow.__new__(app.ExternalAlbumArtWindow)
window._lock = threading.RLock()
window._closed = False
window._commands = queue.Queue()
window._pending_presentation_commands = {}
window._window_title = ''
window._thread = SimpleNamespace(is_alive=lambda: True)
for index in range(100000):
    window.update_title(f'{index} a changing lyric marquee in the popup title')
report['popup'] = {'title_updates':100000, 'queued':window._commands.qsize(), **memory()}
print(json.dumps({'popup':report['popup']}), flush=True)
# Release the artificial backlog/cache before comparing renderer cost.
del window
app._ALBUM_ART_BYTES_CACHE.clear()
app._ALBUM_ART_SOURCE_CACHE.clear()
gc.collect()

width, rows, detail = 200, 32, 9
horizontal = max(2, app.art_detail_horizontal_subcells(detail))
vertical = max(4, app.art_detail_vertical_subcells(detail))
def color(x,y):
    return ((x*3+y*7)%256,(x*5+y*11)%256,(x*13+y*17)%256)
options = dict(columns=width, rows=rows, truncate_top_lines=0, granularity=3,
    spectrum_levels=bytes((x*37)%256 for x in range(width*2)),
    recent_energy=[((x*17)%100)/100 for x in range(width*2)],
    mode=1, color_style=1, processing_style=62, fade_style=1,
    artwork_color_grid=tuple(tuple(color(x,y) for x in range(width*2)) for y in range(rows)),
    artwork_microtile_color_grid=tuple(tuple(color(x,y) for x in range(width*horizontal)) for y in range(rows*vertical)),
    artwork_bar_strength=1., artwork_bar_blend_mode=1, artwork_bar_opacity=.64,
    artwork_background_strength=.3, artwork_microtiles_enabled=True,
    artwork_bar_microtiles_enabled=True, artwork_microtile_detail_mode=detail,
    artwork_bar_microtile_detail_mode=detail)
# Match the public signature; older releases may name opacity differently.
import inspect
options = {key:value for key,value in options.items() if key in inspect.signature(app.render_drcs_visualizer).parameters}
report['render_options'] = {key:value for key,value in options.items() if not isinstance(value,(list,tuple,bytes))}
report['renderer'] = []
hashes = hashlib.sha256()
durations = []
for frame in range(2400):
    options['height_override'] = [.5+.49*math.sin(x*.07+frame*.06) for x in range(width*2)]
    start = time.perf_counter()
    rendered = app.render_drcs_visualizer(**options, rows_out=[])
    elapsed = (time.perf_counter()-start)*1000
    if frame % 60 == 0: hashes.update(rendered.encode('utf-8'))
    durations.append(elapsed)
    if (frame+1)%400 == 0:
        row = {'frames':frame+1, 'median_ms':round(statistics.median(durations),3), 'p95_ms':round(sorted(durations)[int(len(durations)*.95)],3), **memory()}
        report['renderer'].append(row)
        print(json.dumps(row),flush=True)
        durations=[]
report['sampled_frame_sha256']=hashes.hexdigest()
report['caches']={name:function.cache_info()._asdict() for name,function in vars(app).items() if callable(getattr(function,'cache_info',None))}
with open(output, 'x', encoding='utf-8') as stream:
    json.dump(report,stream,indent=2)
