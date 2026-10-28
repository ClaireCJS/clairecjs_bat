"""No terminal writes or audio playback: compare exact frame transport costs."""
import json,math,statistics,sys,time,datetime
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_v519_transport import p,baseline,apply_vt
old=baseline();w=170;h=32
origins=[f'\x1b[?7l\x1b(B\x1b[{y+1};1H\x1b#5' for y in range(h)]
grid=tuple(tuple(((x*3+y*7)%256,(x*5+y*11)%256,(x*13+y*3)%256) for x in range(w*2)) for y in range(h))
micro=tuple(tuple(((x*3+y*2)%256,(x*5+y*3)%256,(x*13+y)%256) for x in range(w*2)) for y in range(h*4))
kwargs=dict(rows=h,truncate_top_lines=0,granularity=3,processing_style=63,artwork_color_grid=grid,artwork_microtile_color_grid=micro,artwork_bar_strength=.65,artwork_bar_blend_mode=1,artwork_bar_opacity=.64,artwork_background_strength=.3,artwork_microtiles_enabled=True,artwork_bar_microtiles_enabled=True,artwork_microtile_detail_mode=9,artwork_bar_microtile_detail_mode=9,semantic_cells_only=True)
results=[]
with mock.patch.object(p,'ARTWORK_SEAM_STRATEGY',5):
 for fps in (30,60,120):
  previous=None;sizes=[[],[]];timings=[[],[]];commands=[[],[]]
  for frame in range(121):
   heights=[.48+.45*math.sin(x*.045+frame*.8/fps) for x in range(w*2)]
   rows=[];p.render_drcs_visualizer(w,b'',heights,height_override=heights,cell_rows_out=rows,**kwargs)
   assert rows and isinstance(rows[0],bytes)
   for index,fn in enumerate((old,p._visualizer_packed_art_delta)):
    start=time.perf_counter();payload,runs=fn(rows,previous,origins);elapsed=time.perf_counter()-start
    if frame:
     sizes[index].append(len(payload));timings[index].append(elapsed*1000);commands[index].append(payload.count('\x1b['))
     if frame%30==0:assert apply_vt(payload,previous)==rows
   previous=rows
  results.append({'input_fps':fps,'width':w,'rows':h,'frames':120,'v518_mean_bytes':statistics.mean(sizes[0]),'v519_mean_bytes':statistics.mean(sizes[1]),'bytes_reduction_percent':100*(1-sum(sizes[1])/sum(sizes[0])),'v518_mean_csi':statistics.mean(commands[0]),'v519_mean_csi':statistics.mean(commands[1]),'v518_encode_median_ms':statistics.median(timings[0]),'v519_encode_median_ms':statistics.median(timings[1])})
report={'scope':'Synthetic artwork/bar movement, exact final cells checked. No console output, no claim of in-game FPS improvement.','python':sys.version,'results':results}
path=ROOT/'tests/reports'/('v519-transport-benchmark-'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+'.json')
with path.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2));print(path)
