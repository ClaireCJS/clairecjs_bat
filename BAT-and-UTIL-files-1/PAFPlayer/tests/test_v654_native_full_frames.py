"""Byte-exact row/payload parity across transport flags and native fallbacks."""
import ast
import itertools
from pathlib import Path
import random
import unittest
from unittest import mock
import PAFPlayer as app

ROOT=Path(__file__).resolve().parents[1]
# Runner supplies this immutable oracle beside the staged player.
baseline=Path(app.__file__).parent/'baseline_v653.py'
if not baseline.is_file():
    baseline=next(parent/'releases/PAFPlayer_v653_idle_art_music_dance.py' for parent in Path(__file__).resolve().parents if (parent/'releases/PAFPlayer_v653_idle_art_music_dance.py').is_file())
source=baseline.read_text(encoding='utf8')
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_visualizer_native_rows_output')
ns=dict(vars(app));exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<V653 output oracle>','exec'),ns)
oracle=ns['_visualizer_native_rows_output']

class NativeFullFrameTests(unittest.TestCase):
    def setUp(self):
        rng=random.Random(654)
        self.rows=[b''.join(bytes(rng.randrange(256) for _ in range(6))+bytes([33+rng.randrange(94)]) for _ in range(12)) for _ in range(3)]

    def render(self,fn,rows,flags):
        cells=[];strings=[]
        value=fn(rows,cells,flags[0],strings,*flags[1:])
        return value,cells,strings

    def test_all_flags_preserve_full_payload_cells_and_rows(self):
        self.assertIsNotNone(app._visualizer_artwork_encoder())
        for flags in itertools.product((False,True),repeat=7):
            with self.subTest(flags=flags):
                self.assertEqual(self.render(oracle,self.rows,flags),self.render(app._visualizer_native_rows_output,self.rows,flags))

    def test_default_transport_flags_and_absent_output_collectors(self):
        for omit_erase in (False,True):
            args=(self.rows,None,False,None,False,False,omit_erase,None,None,None)
            self.assertEqual(oracle(*args),app._visualizer_native_rows_output(*args))

    def test_multiple_sizes_and_repeated_colors_match(self):
        for width,height in ((1,1),(140,48),(240,54)):
            rows=[(bytes([0,255,y%256,255,0,127])+b'~')*width for y in range(height)]
            self.assertEqual(self.render(oracle,rows,(False,)*7),self.render(app._visualizer_native_rows_output,rows,(False,)*7))

    def test_native_path_avoids_python_color_formatting(self):
        with mock.patch.object(app,'_visualizer_packed_art_sgr',side_effect=AssertionError('Python cell loop')):
            self.assertTrue(self.render(app._visualizer_native_rows_output,self.rows,(False,)*7)[0])

    def test_semantic_only_skips_encoding(self):
        with mock.patch.object(app,'_visualizer_native_full_art_lines',side_effect=AssertionError('unneeded encoding')):
            self.assertEqual(('',self.rows,[]),self.render(app._visualizer_native_rows_output,self.rows,(True,False,False,False,False,False,False)))

    def test_missing_native_or_numpy_keeps_legacy_output(self):
        expected=self.render(oracle,self.rows,(False,)*7)
        for helper in ('_visualizer_artwork_encoder','_visualizer_numpy'):
            with self.subTest(helper=helper),mock.patch.object(app,helper,return_value=None):
                self.assertEqual(expected,self.render(app._visualizer_native_rows_output,self.rows,(False,)*7))

    def test_failed_or_malformed_native_output_falls_back(self):
        expected=self.render(oracle,self.rows,(False,)*7)
        for result in (OSError('fixture'),ValueError('dimensions'),('bad output',0)):
            patch=mock.patch.object(app,'_visualizer_packed_art_delta',side_effect=result) if isinstance(result,Exception) else mock.patch.object(app,'_visualizer_packed_art_delta',return_value=result)
            with patch:self.assertEqual(expected,self.render(app._visualizer_native_rows_output,self.rows,(False,)*7))

    def test_empty_frames_and_uneven_rows_use_legacy_path(self):
        for rows in ([],[b''],self.rows+[self.rows[0][:7]]):
            self.assertIsNone(app._visualizer_native_full_art_lines(rows,False))
            self.assertEqual(self.render(oracle,rows,(False,)*7),self.render(app._visualizer_native_rows_output,rows,(False,)*7))

if __name__=='__main__':unittest.main()
