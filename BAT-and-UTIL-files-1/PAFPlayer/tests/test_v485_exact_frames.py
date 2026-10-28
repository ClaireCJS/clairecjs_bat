"""Portable exact-output tests for artwork acceleration and semantic cells."""
import sys,unittest,random
from pathlib import Path
from unittest import mock
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import PAFPlayer as p
class ArtworkFrames(unittest.TestCase):
 def test_exact_frames_and_semantic_colors(self):
  rng=random.Random(485)
  original=p._visualizer_art_frame_rows
  for case in range(30):
   width=12+case%4;rows=(6,24,32)[case%3];crop=case%2;visible=rows-crop
   grid=tuple(tuple((x*17%256,y*31%256,(x+y)*11%256) for x in range(width*2)) for y in range(visible))
   micro=tuple(tuple((x*19%256,y*13%256,(x+y)*7%256) for x in range(width*2)) for y in range(visible*4))
   heights=([0.,1.]*(width) if case==0 else [rng.uniform(-.1,1.1) for _ in range(width*2)])
   kwargs=dict(rows=rows,truncate_top_lines=crop,height_override=heights,granularity=3,processing_style=63,color_reverse=bool(case%2),
    top_blank_by_logical_column=[(x%4 if case%3 else 0) for x in range(width*2)],
    artwork_color_grid=grid,artwork_microtile_color_grid=micro,artwork_bar_strength=(.05,.7,1.)[case%3],
    artwork_bar_blend_mode=case%3,artwork_bar_opacity=(0.,.64,1.)[case%3],artwork_background_strength=.3,
    artwork_microtiles_enabled=True,artwork_bar_microtiles_enabled=True,artwork_microtile_detail_mode=9,artwork_bar_microtile_detail_mode=9,
    feedback_brightness=(1.,1.,1.,.8,1.2)[case%5])
   with mock.patch.object(p,'ARTWORK_SEAM_STRATEGY',5):
    with mock.patch.object(p,'_visualizer_art_frame_rows',return_value=False):
     expected=p.render_drcs_visualizer(width,b'',heights,**kwargs)
    cells=[];got=p.render_drcs_visualizer(width,b'',heights,cell_rows_out=cells,**kwargs)
    self.assertEqual(expected,got,f'case {case}')
    if cells:
     semantic=[];text=p.render_drcs_visualizer(width,b'',heights,cell_rows_out=semantic,semantic_cells_only=True,**kwargs)
     self.assertEqual('',text);self.assertEqual(cells,semantic)
     self.assertEqual(visible,len(cells));self.assertTrue(all(len(row)==width*7 for row in cells))
     for row in cells:
      for index in range(width):
       color=row[index*7:index*7+6]
       self.assertEqual(p._visualizer_ansi_fg_bg_cached(*color),p._visualizer_cell_sgr(color))
   self.assertLessEqual(len(p._VISUALIZER_ART_FRAME_ARRAY_CACHE),4)
 def test_native_encoder_equals_fallback(self):
  rng=random.Random(486)
  previous=None
  for width in (12,170,300):
   previous=None
   for frame in range(5):
    rows=[bytes(rng.randrange(256) if i%7<6 else rng.randrange(33,127) for i in range(width*7)) for _ in range(4)]
    if frame==2:rows=previous
    if frame==3:rows[1]=previous[1]
    origins=[f'\033[?7l\033(B\033[{i+10};1H\033#5' for i in range(4)]
    native=p._visualizer_packed_art_delta(rows,previous,origins)
    with mock.patch.object(p,'_visualizer_artwork_encoder',return_value=None):
     fallback=p._visualizer_packed_art_delta(rows,previous,origins)
    self.assertEqual(fallback,native)
    if frame==2:self.assertEqual(('',0),native)
    previous=rows
 def test_optional_numpy_fallback(self):
  with mock.patch.object(p,'_visualizer_numpy',return_value=None):
   self.assertTrue(p.render_drcs_visualizer(16,bytes([10]*32),[.5]*32,rows=6,truncate_top_lines=0))
 def test_plain_semantic_color(self):
  self.assertEqual(p._visualizer_ansi_fg_bg_cached(1,2,3,-1,-1,-1),p._visualizer_cell_sgr((1,2,3)))
if __name__=='__main__':unittest.main()
