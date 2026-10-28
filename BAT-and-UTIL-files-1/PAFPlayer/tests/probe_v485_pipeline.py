import sys,json,os,time,statistics
from pathlib import Path
from unittest import mock
sys.dont_write_bytecode=True
import probe_v482_track_renderer as probe
s=json.loads(Path(__file__).with_name('v485-live-settings.json').read_text(encoding='utf-8-sig'))
probe.TRACK=Path(s['track']['path'])
local,ns=probe.capture_renderer(170,47)
show=local['show_status'];cells=dict(zip(show.__code__.co_freevars,show.__closure__))
print({k:local.get(k) for k in ('DRCS_ROW','drcs_rows','UI_ROWS','track_artwork_allowed','visualizer_width','visualizer_source_rows','truncate_top_visualizer_lines','visualizer_transport_mode')})
print('matching',[(k,s[k]) for k in cells if k in s and isinstance(s[k],(bool,int,float,str))])
print('globals',{k:ns[k] for k in ns if k.startswith('ART_COLOR_VISUALIZER') and not callable(ns[k]) and len(str(ns[k]))<100})
# Complete pipeline, with the same renderer arguments and actual 170x47 terminal.
ns.update(ART_COLOR_VISUALIZER_REPRESENTATION='both',ART_COLOR_VISUALIZER_BAR_STRENGTH=1.,ART_COLOR_VISUALIZER_BAR_OPACITY=.64,ART_COLOR_VISUALIZER_BLACK_STRENGTH=.3,ART_COLOR_VISUALIZER_BAR_BLEND_MODE=1)
probe.app.ARTWORK_SEAM_STRATEGY=5
for k,cell in cells.items():
 try:cell.cell_contents
 except ValueError:cell.cell_contents=False
 if k in s and isinstance(s[k],(bool,int,float,str)) and k!='visualizer_input_source':cell.cell_contents=s[k]
cells['truncate_top_visualizer_lines'].cell_contents=0
cells['visualizer_transport_mode'].cell_contents='semantic-cell'
cells['drcs_timeline'].cell_contents=probe.app.build_audio_spectrum_timeline(probe.TRACK,340,duration_limit=20.)
cells['spectrum_analysis_columns'].cell_contents=340
writes=[];ns['write_console']=writes.append
with mock.patch.object(probe.app.shutil,'get_terminal_size',return_value=os.terminal_size((170,47))):
 for i in range(8):show(5+i/60,'>',visualizer_only=True)
 tms=[];sizes=[]
 for i in range(120):
  writes.clear();t=time.perf_counter();show(6+i/60,'>',visualizer_only=True);tms.append((time.perf_counter()-t)*1000);sizes.append(sum(map(len,writes)))
 print('pipeline',json.dumps(dict(median_ms=statistics.median(tms),mean_ms=statistics.mean(tms),chars=statistics.mean(sizes),semantic_cache_rows=len(cells['last_visualizer_cells'].cell_contents or []))),flush=True)
