"""Measure and compare floating cue masks without creating windows or playing audio."""
import ast,sys,time,statistics,json,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import PAFPlayer as p
NAMES={'build_floating_lyric_mask','resolve_artwork_pillow_font','resolve_artwork_pillow_emoji_font','_pillow_char_is_emojiish','_pillow_mixed_font_runs','_pillow_run_advance','_pillow_mixed_text_width','_pillow_font_metrics','_pillow_mixed_line_metrics','_pillow_draw_mixed_line','_pillow_draw_colored_emoji_runs'}
def load(path):
 tree=ast.parse(path.read_text(encoding='utf-8-sig'));ns=dict(vars(p));ns.update(state={},karaoke_shadow_size=lambda target:.06)
 for node in ast.walk(tree):
  if isinstance(node,ast.FunctionDef) and node.name in NAMES:
   exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
 return ns
class CueMasks(unittest.TestCase):
 def test_cue_cancels_stale_animation_before_upload(self):
  from unittest.mock import Mock
  tree=ast.parse((ROOT/'PAFPlayer.py').read_text(encoding='utf-8-sig'))
  node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='render_floating_lyric')
  window=Mock();canvas=Mock();canvas.winfo_width.return_value=900;canvas.winfo_height.return_value=300
  state=dict(floating_window=window,floating_canvas=canvas,floating_edit_mode=True,floating_color_after='stale-timer',lyric_floating='')
  ns=dict(vars(p));ns['state']=state
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<cue>','exec'),ns)
  ns['render_floating_lyric']()
  window.after_cancel.assert_called_once_with('stale-timer')
  self.assertIsNone(state['floating_color_after'])
 def test_masks_and_layout_match_v485(self):
  old=load(ROOT/'releases/PAFPlayer_v485_artwork_fps_and_responsive_bass.py');new=load(ROOT/'PAFPlayer.py')
  timing={'V485':[],'V486':[]}
  for i in range(24):
   state=dict(floating_autosize=i%4!=0,floating_font_scale=1.2,popup_color_emoji_enabled=bool(i%2),floating_justification=('left','center','right')[i%3])
   args=((900,300) if i%2 else (1200,500))+ (('Ocean man take me by the hand','Take me to the land that you understand 🌊','⛤ ❶ Hello world')[i%3],)
   out=[]
   for key,ns in [('V485',old),('V486',new)]:
    ns['state'].update(state);start=time.perf_counter();v=ns['build_floating_lyric_mask'](*args);timing[key].append((time.perf_counter()-start)*1000);out.append(v)
   a,b=out;self.assertEqual(a[0].size,b[0].size);self.assertEqual(a[0].tobytes(),b[0].tobytes());self.assertEqual(a[1:4],b[1:4]);self.assertEqual(a[4].size,b[4].size)
   if a[5] is not None:self.assertEqual(a[5].tobytes(),b[5].tobytes())
  print(json.dumps({k:{'median_ms':statistics.median(v),'max_ms':max(v)} for k,v in timing.items()}))
  self.assertGreater(new['resolve_artwork_pillow_font'].cache_info().hits,0)
if __name__=='__main__':unittest.main()
