"""V486 exact rendering/state equivalence against immutable V485 source."""
import ast,sys,unittest,random,tempfile
from pathlib import Path
from unittest import mock
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));cache=ROOT/'tests/v486-temp';cache.mkdir(exist_ok=True);tempfile.tempdir=str(cache)
import PAFPlayer as p
BASE=ROOT/'releases/PAFPlayer_v485_artwork_fps_and_responsive_bass.py'
tree=ast.parse(BASE.read_text(encoding='utf-8-sig'))
ns=dict(vars(p))
for name in ('render_drcs_visualizer','apply_visualizer_persistence'):
 node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(BASE),'exec'),ns)
class ExactFrames(unittest.TestCase):
 maxDiff=300
 def test_fused_composition_matches_v485(self):
  rng=random.Random(486)
  self.assertIsNotNone(p._visualizer_luma_composer(),'Run on Windows x64 to verify the native composer')
  for case in range(72):
   width=(12,19,37)[case%3];rows=(6,24,32,38)[case%4];crop=(0,1,3)[case%3];visible=rows-crop
   grid=tuple(tuple(tuple(rng.randrange(256) for _ in range(3)) for x in range(width*2)) for y in range(visible))
   mode=(1,2,3,4,5,6,9)[case%7];sx=p.art_detail_horizontal_subcells(mode);sy=p.art_detail_vertical_subcells(mode)
   micro=tuple(tuple(tuple(rng.randrange(256) for _ in range(3)) for x in range(width*sx)) for y in range(visible*sy))
   heights=[rng.choice([0.,1.,.5,1/16,15/16]) if case%4==0 else rng.uniform(-.1,1.1) for _ in range(width*2)]
   kwargs=dict(rows=rows,truncate_top_lines=crop,height_override=heights,granularity=3,processing_style=(63,62,47)[case%3],color_reverse=bool(case%2),
    top_blank_by_logical_column=[x%5 if case%2 else 0 for x in range(width*2)],
    artwork_color_grid=grid,artwork_microtile_color_grid=micro,artwork_bar_strength=(.001,.05,.499,.7,1.)[case%5],
    artwork_bar_blend_mode=1,artwork_bar_opacity=(0.,.001,.5,.64,1.)[case%5],artwork_background_strength=.3,
    artwork_microtiles_enabled=True,artwork_bar_microtiles_enabled=True,artwork_microtile_detail_mode=mode,artwork_bar_microtile_detail_mode=mode,
    omit_big_off=bool(case%2),omit_erase_eol=bool(case%3),use_cud_row_advance=bool(case%2),force_row_column_one=bool(case%3),disable_autowrap_during_paint=bool(case%2))
   with mock.patch.object(p,'ARTWORK_SEAM_STRATEGY',5):
    expected=ns['render_drcs_visualizer'](width,b'',heights,**kwargs)
    with mock.patch.object(p,'_visualizer_native_luma_rows',wraps=p._visualizer_native_luma_rows) as fast:
     cells=[];got=p.render_drcs_visualizer(width,b'',heights,cell_rows_out=cells,**kwargs)
     self.assertEqual(1,fast.call_count,case)
    self.assertEqual(expected,got,f'case {case}')
    with mock.patch.object(p,'_visualizer_luma_composer',return_value=None):
     self.assertEqual(expected,p.render_drcs_visualizer(width,b'',heights,**kwargs))
    before=[];after=[]
    ns['render_drcs_visualizer'](width,b'',heights,cell_rows_out=before,semantic_cells_only=True,**kwargs)
    self.assertEqual('',p.render_drcs_visualizer(width,b'',heights,cell_rows_out=after,semantic_cells_only=True,**kwargs))
    self.assertEqual(before,after,case)
    self.assertLessEqual(len(p._VISUALIZER_NATIVE_LUMA_CACHE),4)
 def test_ghost_history_state_and_switches_match_v485(self):
  rng=random.Random(42);a={};b={}
  for tick in range(180):
   n=(12,37,338)[tick//60];values=[rng.uniform(-.2,1.3) for _ in range(n)]
   mode=2 if tick%11 else rng.randrange(1,13)
   self.assertEqual(ns['apply_visualizer_persistence'](values,a,mode,.012),p.apply_visualizer_persistence(values,b,mode,.012))
   self.assertEqual(a,b)
if __name__=='__main__':unittest.main()
