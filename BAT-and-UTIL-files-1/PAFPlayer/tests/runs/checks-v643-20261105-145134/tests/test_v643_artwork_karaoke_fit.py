"""Actual Tk/Pillow artwork cue fitting, isolated from playback and settings."""
import contextlib
import math
import tkinter as tk
import unittest
from unittest import mock

from PIL import ImageDraw
import PAFPlayer as app
from test_v642_artwork_chrome import functions


class ArtworkFitTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.state = dict(border_pixels=5, lyric_font_scale=1.0,
                          popup_emojimax_enabled=True, artwork_solution_show=True)
        self.ns = dict(vars(app), root=self.root, state=self.state,
                       widget_dpi=lambda _: 144,
                       karaoke_shadow_size=lambda _: 0.05)
        functions(self.ns, 'artwork_solutions_active', 'resolve_artwork_pillow_font',
                  'resolve_artwork_pillow_emoji_font', '_pillow_char_is_emojiish',
                  '_pillow_font_for_run', '_pillow_mixed_font_runs', '_pillow_render_runs',
                  '_pillow_run_advance', '_pillow_mixed_text_width', '_pillow_font_metrics',
                  '_pillow_mixed_line_metrics', '_pillow_draw_mixed_line',
                  '_pillow_draw_colored_emoji_runs', 'fit_artwork_lyric_tk_layout',
                  'build_artwork_plasma_mask', 'adjust_artwork_lyric_zoom')

    def tearDown(self):
        self.root.destroy()

    def check_native(self, width, height, text):
        layout = self.ns['fit_artwork_lyric_tk_layout'](width, height, text)
        canvas = tk.Canvas(self.root, width=width, height=height, bd=0, highlightthickness=0)
        for i, line in enumerate(layout['lines']):
            y = layout['top'] + i * layout['line_height']
            for offset in (0, layout['shadow']):
                canvas.create_text(layout['center_x'] + offset, y + offset,
                                   text=line, font=layout['font'], anchor='n')
        bounds = canvas.bbox('all')
        self.assertGreaterEqual(bounds[0], 0)
        self.assertGreaterEqual(bounds[1], 0)
        self.assertLessEqual(bounds[2], width)
        self.assertLessEqual(bounds[3], height)
        used_width = max(layout['font'].measure(s) for s in layout['lines'])
        used_height = layout['line_height'] * len(layout['lines'])
        canvas.destroy()
        return layout, max(used_width / (width-30), used_height / (height-20))

    def check_pillow(self, width, height, text):
        mask, origin, shadow, wrapped, font, overlay = self.ns['build_artwork_plasma_mask'](width, height, text)
        self.assertGreaterEqual(origin[0], 0)
        self.assertGreaterEqual(origin[1], 0)
        self.assertLessEqual(origin[0] + mask.width, width)
        self.assertLessEqual(origin[1] + mask.height, height)
        self.assertIsNotNone(mask.getbbox())
        if overlay is not None:
            self.assertEqual(mask.size, overlay.size)
        return font.size, max(mask.width / (width-30), mask.height / (height-20)), wrapped

    def test_short_cues_expand_in_both_renderers_without_clipping(self):
        for text in ('Hey', "Don't want to be", 'Go!'):
            for size in ((900, 540), (1600, 900), (340, 600)):
                with self.subTest(text=text, size=size, renderer='Tk'):
                    _, fill = self.check_native(*size, text)
                    self.assertGreater(fill, .85)
                with self.subTest(text=text, size=size, renderer='Pillow'):
                    _, fill, _ = self.check_pillow(*size, text)
                    self.assertGreater(fill, .85)

    def test_long_wrapped_lines_stay_inside_portrait_and_landscape_windows(self):
        text = 'Take the long way home and sing along until the morning comes'
        for size in ((320, 210), (700, 1050), (1800, 400)):
            with self.subTest(size=size):
                layout, fill = self.check_native(*size, text)
                self.assertGreater(fill, .8)
                _, fill, wrapped = self.check_pillow(*size, text)
                self.assertGreater(fill, .8)
                self.assertEqual(text.split(), ' '.join(layout['lines']).split())
                self.assertEqual(text.split(), wrapped.split())

    def test_resize_grows_short_cue_beyond_old_260_point_cap(self):
        small, _ = self.check_native(640, 360, 'Hey')
        big, _ = self.check_native(3840, 2160, 'Hey')
        self.assertGreater(big['font_size'], small['font_size'] * 4)
        self.assertGreater(big['font_size'], 260)
        small_px, _, _ = self.check_pillow(640, 360, 'Hey')
        big_px, _, _ = self.check_pillow(3840, 2160, 'Hey')
        self.assertGreater(big_px, small_px * 4)
        self.assertGreater(big_px, 520)

    def test_manual_zoom_reduces_fitted_size_and_legacy_large_zoom_stays_bounded(self):
        full_tk, _ = self.check_native(900, 540, 'Hey')
        full_px, _, _ = self.check_pillow(900, 540, 'Hey')
        self.state['lyric_font_scale'] = .5
        small_tk, _ = self.check_native(900, 540, 'Hey')
        small_px, _, _ = self.check_pillow(900, 540, 'Hey')
        self.assertAlmostEqual(full_tk['font_size'] * .5, small_tk['font_size'], delta=1)
        self.assertAlmostEqual(full_px * .5, small_px, delta=1)
        self.state['lyric_font_scale'] = 2.5
        big_tk, _ = self.check_native(900, 540, 'Hey')
        big_px, _, _ = self.check_pillow(900, 540, 'Hey')
        self.assertEqual(full_tk['font_size'], big_tk['font_size'])
        self.assertEqual(full_px, big_px)
        self.ns['save_external_album_art_lyric_font_scale'] = mock.Mock()
        self.ns['redraw_artwork_lyric_layer'] = mock.Mock()
        self.ns['adjust_artwork_lyric_zoom'](-1)
        self.assertAlmostEqual(.9, self.state['lyric_font_scale'])
        self.ns['save_external_album_art_lyric_font_scale'].assert_called_once_with(.9)

    def test_emoji_answers_and_shadow_are_reserved_in_fit(self):
        plain, _ = self.check_native(800, 600, 'Hey')
        plain_px, _, _ = self.check_pillow(800, 600, 'Hey')
        self.state.update(lyric_solutions_artwork=[('🔥', 'fire')],
                          artwork_solution_size=50, artwork_solution_distance=20)
        answers, _ = self.check_native(800, 600, 'Hey')
        answers_px, _, _ = self.check_pillow(800, 600, 'Hey')
        self.assertLess(answers['font_size'], plain['font_size'])
        self.assertLess(answers_px, plain_px)
        for above in (False, True):
            self.state['artwork_solution_above'] = above
            for colored in (False, True):
                self.state['popup_color_emoji_enabled'] = colored
                self.check_pillow(800, 600, 'We are 🔥 tonight')

    def test_pillow_pixel_size_is_independent_of_monitor_dpi(self):
        sizes = []
        for dpi in (96, 144, 192):
            self.ns['widget_dpi'] = lambda _, dpi=dpi: dpi
            sizes.append(self.check_pillow(900, 540, 'Hey')[0])
        self.assertEqual(1, len(set(sizes)))

    def test_4k_fitting_stays_logarithmic(self):
        for name, call in (('resolve_artwork_pillow_font', lambda: self.check_pillow(3840, 2160, 'Hey')),
                           ('resolve_artwork_pillow_emoji_font', lambda: self.check_pillow(3840, 2160, 'Hey'))):
            with mock.patch.dict(self.ns, {name: mock.Mock(wraps=self.ns[name])}):
                call()
                self.assertLessEqual(self.ns[name].call_count, 14)


if __name__ == '__main__':
    unittest.main()
