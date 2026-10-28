"""V486 reproducible renderer fixture from the current instance; no audio playback."""
import sys,json,os,time,statistics,cProfile,pstats,io,tempfile
from pathlib import Path
from unittest import mock
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'tests'/'v486-temp';CACHE.mkdir(exist_ok=True);tempfile.tempdir=str(CACHE)
import probe_v482_track_renderer as probe

def fixture():
 s=json.loads((ROOT/'tests/v486-live-settings.json').read_text(encoding='utf-8-sig'))
 probe.TRACK=Path(s['track']['path']);p=probe.app
 local,ns=probe.capture_renderer(170,47)
 show=local['show_status'];cells=dict(zip(show.__code__.co_freevars,show.__closure__))
 ns.update(ART_COLOR_VISUALIZER_REPRESENTATION=p.ART_COLOR_VISUALIZER_REPRESENTATIONS[s['art_color_representation']],ART_COLOR_VISUALIZER_BAR_STRENGTH=s['art_color_bar_strength']/100,ART_COLOR_VISUALIZER_BAR_OPACITY=s['art_color_bar_opacity']/100,ART_COLOR_VISUALIZER_BLACK_STRENGTH=s['art_color_black_strength']/100,ART_COLOR_VISUALIZER_BAR_BLEND_MODE=s['art_color_bar_blend_mode'])
 p.ARTWORK_SEAM_STRATEGY=s['artwork_seam_strategy']
 for k,cell in cells.items():
  try:cell.cell_contents
  except ValueError:cell.cell_contents=False
  if k in s and isinstance(s[k],(bool,int,float,str)) and k!='visualizer_input_source':cell.cell_contents=s[k]
 cells['truncate_top_visualizer_lines'].cell_contents=s['truncate_visualizer_rows']
 cells['visualizer_transport_mode'].cell_contents=s['visualizer_perf']['transport_mode']
 cells['drcs_timeline'].cell_contents=p.build_audio_spectrum_timeline(probe.TRACK,340,duration_limit=20.)
 cells['spectrum_analysis_columns'].cell_contents=340
 ns['write_console']=lambda text:None
 return p,local,ns,show

if __name__=='__main__':
 p,local,ns,show=fixture()
 with mock.patch.object(p.shutil,'get_terminal_size',return_value=os.terminal_size((170,47))):
  for i in range(10):show(5+i/120,'>',visualizer_only=True)
  times=[]
  for i in range(180):
   t=time.perf_counter();show(6+i/120,'>',visualizer_only=True);times.append((time.perf_counter()-t)*1000)
  print(json.dumps({'version':p.PROGRAM_VERSION,'mean_ms':statistics.mean(times),'median_ms':statistics.median(times)}),flush=True)
  c=cProfile.Profile();c.enable()
  for i in range(120):show(8+i/120,'>',visualizer_only=True)
  c.disable();pstats.Stats(c).sort_stats('cumtime').print_stats(24)
