import sys,json,cProfile,pstats,io,time,statistics,math
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import PAFPlayer as p
s=json.loads((Path(__file__).with_name('v485-live-settings.json')).read_text(encoding='utf-8-sig'))
w=170;r=32
p.ARTWORK_SEAM_STRATEGY=s['artwork_seam_strategy']
g=p.album_art_visualizer_color_grid(s['track']['path'],w*2,r,2)
m=s['drcs_art_microtile_mode'];h=p.art_detail_horizontal_subcells(m);v=p.art_detail_vertical_subcells(m)
mg=p.album_art_visualizer_color_grid(s['track']['path'],w*h,r*v,h,v)
kw=dict(mode=s['visualizer_mode'],color_style=s['color_style'],color_reverse=s['color_reverse'],processing_style=s['processing_style'],rows=r,granularity=3,artwork_color_grid=g,artwork_microtile_color_grid=mg,artwork_bar_strength=1.,artwork_bar_blend_mode=1,artwork_bar_opacity=.64,artwork_background_strength=.3,artwork_microtiles_enabled=True,artwork_bar_microtiles_enabled=True,artwork_microtile_detail_mode=m,artwork_bar_microtile_detail_mode=m)
def frame(i):
    heights=[.5+.45*math.sin(x*.04+i*.07) for x in range(w*2)]
    return p.render_drcs_visualizer(w,b'',heights,height_override=heights,**kw)
for i in range(8):frame(i)
times=[]
for i in range(120):
 t=time.perf_counter();frame(i);times.append((time.perf_counter()-t)*1000)
print(json.dumps(dict(width=w,rows=r,art=bool(g),microart=bool(mg),mean_ms=statistics.mean(times),median_ms=statistics.median(times))))
c=cProfile.Profile();c.enable()
for i in range(30):frame(i)
c.disable();pstats.Stats(c).sort_stats('cumtime').print_stats(22)
