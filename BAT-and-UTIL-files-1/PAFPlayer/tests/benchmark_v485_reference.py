"""Exact-output regression and interleaved timings against pre-V485 renderer."""
import ast,json,sys,time,statistics,math,random
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import PAFPlayer as p
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'PAFPlayer.py.bak.202610011300.replaced-by-chatgpt.bak'
node=next(n for n in ast.parse(old.read_text(encoding='utf-8-sig')).body if isinstance(n,ast.FunctionDef) and n.name=='render_drcs_visualizer')
ns=dict(vars(p));exec(compile(ast.Module(body=[node],type_ignores=[]),str(old),'exec'),ns)
reference=ns['render_drcs_visualizer']
s=json.loads((ROOT/'tests/v485-live-settings.json').read_text(encoding='utf-8-sig'))
p.ARTWORK_SEAM_STRATEGY=5
w=170;r=32;m=9
art=p.album_art_visualizer_color_grid(s['track']['path'],w*2,r,2)
micro=p.album_art_visualizer_color_grid(s['track']['path'],w*2,r*4,2,4)
kw=dict(rows=r,truncate_top_lines=0,granularity=3,processing_style=63,color_reverse=True,artwork_color_grid=art,artwork_microtile_color_grid=micro,artwork_bar_strength=1.,artwork_bar_blend_mode=1,artwork_bar_opacity=.64,artwork_background_strength=.3,artwork_microtiles_enabled=True,artwork_bar_microtiles_enabled=True,artwork_microtile_detail_mode=m,artwork_bar_microtile_detail_mode=m)
def args(i):
 h=[.5+.45*math.sin(x*.04+i*.07) for x in range(w*2)]
 return (w,b'',h),dict(kw,height_override=h)
for i in range(20):
 a,k=args(i);want=reference(*a,**k);got=p.render_drcs_visualizer(*a,**k)
 if want!=got:
  pos=next(j for j,(x,y) in enumerate(zip(want,got)) if x!=y)
  raise AssertionError((i,pos,want[max(0,pos-50):pos+100],got[max(0,pos-50):pos+100]))
print('20 changing real-art frames byte-identical',flush=True)
for label,renderer in [('old',reference),('new',p.render_drcs_visualizer),('new-semantic',p.render_drcs_visualizer),('old',reference)]:
 times=[];size=0
 for i in range(120):
  a,k=args(i)
  if label=='new-semantic':k.update(cell_rows_out=[],semantic_cells_only=True)
  t=time.perf_counter();output=renderer(*a,**k);times.append((time.perf_counter()-t)*1000);size+=len(output)
 print(json.dumps(dict(path=label,median_ms=statistics.median(times),mean_ms=statistics.mean(times),chars=size)),flush=True)
