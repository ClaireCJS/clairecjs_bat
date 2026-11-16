"""Exact cold-layout parity and bounded reuse of artwork across lyric gaps."""
import io
import random
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import PAFPlayer as app


class ArtworkCellParityTests(unittest.TestCase):
    def setUp(self):
        self.seam=mock.patch.object(app,'ARTWORK_SEAM_STRATEGY',5);self.seam.start()
        self.addCleanup(self.seam.stop)
        app._VISUALIZER_ART_DETAIL_GRID_CACHE.clear()
        app._VISUALIZER_ART_SCALE_CACHE.clear()

    def compare(self,grid,rows,width,strength,mode,layout):
        app._VISUALIZER_ART_DETAIL_GRID_CACHE.clear()
        fast=app._visualizer_art_microtiles(grid,rows,width,strength,mode,layout)
        app._VISUALIZER_ART_DETAIL_GRID_CACHE.clear()
        with mock.patch.object(app,'_visualizer_numpy',return_value=None):
            scalar=app._visualizer_art_microtiles(grid,rows,width,strength,mode,layout)
        self.assertEqual(scalar,fast)
        return fast

    def test_every_detail_mode_matches_scalar_at_multiple_strengths(self):
        rng=random.Random(650)
        grid=tuple(tuple(tuple(rng.randrange(256) for _ in range(3)) for _ in range(9)) for _ in range(10))
        for mode in range(1,len(app.ART_MICROTILE_DETAIL_MODE_GEOMETRIES)):
            for layout in (2,3,6):
                for strength in (0,.123,.5,1.0):
                    with self.subTest(mode=mode,layout=layout,strength=strength):
                        self.compare(grid,2,3,strength,mode,layout)

    def test_uniform_tied_pairs_and_half_rounding_match(self):
        for colors in (((1,3,5),)*8,((0,0,0),(255,255,255))*4,
                       ((0,0,0),(0,2,0),(2,0,0),(2,2,0))*2):
            grid=tuple(tuple(colors[(y*4+x)%8] for x in range(4)) for y in range(8))
            for strength in (.5,1):
                with self.subTest(colors=colors,strength=strength):self.compare(grid,2,2,strength,9,3)

    def test_rectangular_sampling_and_cropped_source_match(self):
        rng=random.Random(651)
        grid=tuple(tuple(tuple(rng.randrange(256) for _ in range(3)) for x in range(13)) for y in range(15))
        self.compare(grid,3,4,.817,2,6)

    def test_return_to_prepared_geometry_reuses_cells_and_cache_is_bounded(self):
        grid=tuple(tuple((30,70,110) for x in range(4)) for y in range(8))
        result=app._visualizer_art_microtiles(grid,2,2,.5,9,3)
        with mock.patch.object(app,'_visualizer_drcs_microtiles_numpy',side_effect=AssertionError('rebuilt warm geometry')):
            self.assertIs(result,app._visualizer_art_microtiles(grid,2,2,.5,9,3))
        for strength in range(1,30):app._visualizer_art_microtiles(grid,2,2,strength/31,9,3)
        self.assertLessEqual(len(app._VISUALIZER_ART_DETAIL_GRID_CACHE),12)

    def test_other_seam_strategies_keep_their_original_path(self):
        grid=tuple(tuple((30,70,110) for x in range(4)) for y in range(8))
        with mock.patch.object(app,'ARTWORK_SEAM_STRATEGY',0),mock.patch.object(app,'_visualizer_drcs_microtiles_numpy',side_effect=AssertionError('wrong strategy')):
            self.assertTrue(app._visualizer_art_microtiles(grid,2,2,.5,9,3))

    def test_unavailable_numpy_and_small_ragged_inputs_fall_back(self):
        grid=(((30,70,110),)*4,)*8
        expected=app._visualizer_art_microtiles(grid,2,2,.5,9,3)
        app._VISUALIZER_ART_DETAIL_GRID_CACHE.clear()
        with mock.patch.object(app,'_visualizer_numpy',return_value=None):
            self.assertEqual(expected,app._visualizer_art_microtiles(grid,2,2,.5,9,3))
        self.assertIsNone(app._visualizer_drcs_microtiles_numpy((grid[0],grid[1][:2]),2,2,500,9,3))


class ArtworkSourceReuseTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='v650-art-'))
        self.track=self.root/'fixture.flac';self.track.write_bytes(b'fixture')
        self.cache=mock.patch.object(app,'_VISUALIZER_ART_VARIANTS_CACHE',(None,()));self.cache.start()
        self.addCleanup(self.cache.stop)
        app.album_art_visualizer_color_grid.cache_clear()

    def test_compact_expanded_and_microtile_grids_share_one_extraction(self):
        from PIL import Image
        stream=io.BytesIO();Image.new('RGB',(64,64),(32,64,96)).save(stream,format='PNG')
        with mock.patch.object(app,'extract_album_art_variants',return_value=[stream.getvalue()]) as extract, mock.patch.object(app,'terminal_cell_pixel_size_nonintrusive',return_value=(10,20)):
            for columns,rows,horizontal,vertical in ((24,12,2,1),(24,18,2,1),(24,72,2,4),(24,48,2,4)):
                grid=app.album_art_visualizer_color_grid(str(self.track),columns,rows,horizontal,vertical)
                self.assertEqual(rows,len(grid));self.assertTrue(all(len(r)==columns for r in grid))
            self.assertEqual(1,extract.call_count)
            self.assertEqual((self.track,4),extract.call_args.args)

    def test_changed_track_signature_invalidates_and_only_one_source_is_retained(self):
        with mock.patch.object(app,'_album_art_variants_flight_key',side_effect=[('a',1,4,4),('a',1,4,4),('a',2,4,4),('a',2,4,4)]) as key, mock.patch.object(app,'extract_album_art_variants',side_effect=[[b'first'],[b'second']]) as extract:
            self.assertEqual((b'first',),app._visualizer_album_art_variants(self.track))
            self.assertEqual((b'second',),app._visualizer_album_art_variants(self.track))
            self.assertEqual(2,extract.call_count)
            self.assertEqual((b'second',),app._VISUALIZER_ART_VARIANTS_CACHE[1])

    def test_large_sources_are_returned_but_never_retained(self):
        with mock.patch.object(app,'VISUALIZER_ART_VARIANTS_CACHE_MAX_BYTES',5),mock.patch.object(app,'extract_album_art_variants',return_value=[b'123456']) as extract:
            for _ in range(2):self.assertEqual((b'123456',),app._visualizer_album_art_variants(self.track))
            self.assertEqual(2,extract.call_count);self.assertEqual((None,()),app._VISUALIZER_ART_VARIANTS_CACHE)

    def test_extraction_error_does_not_poison_next_request(self):
        with mock.patch.object(app,'extract_album_art_variants',side_effect=[OSError('fixture'),[b'ok']]):
            with self.assertRaises(OSError):app._visualizer_album_art_variants(self.track)
            self.assertEqual((b'ok',),app._visualizer_album_art_variants(self.track))


if __name__=='__main__':unittest.main()
