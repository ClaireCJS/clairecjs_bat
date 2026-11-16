"""Color equivalence, bounded Python work, and immediate cue/deferred animation."""
import contextlib
import random
import unittest
from types import SimpleNamespace
from unittest import mock

from PIL import Image, ImageDraw
import PAFPlayer as app
from test_v642_artwork_chrome import functions


def original_color(configured, inherit, box, image=None, origin=(0, 0), mask=None):
    """Independent V645 pixel-search oracle, retained to detect changed colors."""
    fallback = app.normalize_lyric_solution_setting('color', configured)
    if not inherit or image is None:
        return fallback
    left, top, right, bottom = map(int, box)
    ox, oy = map(int, origin)
    x0, x1 = max(0, left-ox), min(image.width, right-ox)
    y0, y1 = max(0, top-oy), min(image.height, bottom-oy)
    if mask is not None:
        x1, y1 = min(x1, mask.width), min(y1, mask.height)
    if x0 >= x1 or y0 >= y1:
        return fallback
    rows = sorted(range(y0, y1), key=lambda y: abs(y-(y0+y1-1)/2))
    for threshold in (200, 96):
        for x in range(x0, x1):
            for y in rows:
                if mask is not None and mask.getpixel((x, y)) < threshold:
                    continue
                pixel = image.getpixel((x, y))
                if len(pixel) < 3 or (len(pixel) >= 4 and pixel[3] < threshold):
                    continue
                return '#%02x%02x%02x' % pixel[:3]
    return fallback


class InheritedColorTests(unittest.TestCase):
    def test_randomized_exact_v645_equivalence_and_no_mutation(self):
        rng = random.Random(646)
        for case in range(300):
            width, height = rng.randrange(1, 30), rng.randrange(1, 30)
            mode = 'RGB' if case % 3 == 0 else 'RGBA'
            image = Image.new(mode, (width, height))
            values = [0, 95, 96, 97, 199, 200, 201, 255]
            image.putdata([tuple(rng.randrange(256) for _ in range(3)) +
                           ((rng.choice(values),) if mode == 'RGBA' else ())
                           for _ in range(width*height)])
            mask = None
            if case % 4:
                mask = Image.new('L', (rng.randrange(1, 34), rng.randrange(1, 34)))
                mask.putdata([rng.choice(values) for _ in range(mask.width*mask.height)])
            origin = rng.randrange(-10, 10), rng.randrange(-10, 10)
            box = (rng.randrange(-10, 15), rng.randrange(-10, 15),
                   rng.randrange(1, 45), rng.randrange(1, 45))
            before = (image.tobytes(), mask.tobytes() if mask is not None else None)
            with self.subTest(case=case, mode=mode):
                self.assertEqual(original_color('#aabbcc', True, box, image, origin, mask),
                                 app.emojimax_solution_label_color('#aabbcc', True, box, image, origin, mask))
                self.assertEqual(before, (image.tobytes(), mask.tobytes() if mask is not None else None))

    def test_solid_threshold_beats_leftmost_translucent_pixel(self):
        image = Image.new('RGBA', (4, 5))
        image.putpixel((0, 2), (255, 0, 0, 199))
        image.putpixel((3, 0), (0, 255, 0, 200))
        self.assertEqual('#00ff00', app.emojimax_solution_label_color('#abcdef', True, (0, 0, 4, 5), image))
        image.putpixel((3, 0), (0, 255, 0, 95))
        self.assertEqual('#ff0000', app.emojimax_solution_label_color('#abcdef', True, (0, 0, 4, 5), image))

    def test_center_ties_favor_upper_row_with_clipping_and_origin(self):
        for height, upper, lower in ((6, 2, 3), (7, 2, 4)):
            image = Image.new('RGBA', (4, height+2))
            image.putpixel((1, upper+1), (12, 34, 56, 255))
            image.putpixel((1, lower+1), (65, 43, 21, 255))
            self.assertEqual('#0c2238', app.emojimax_solution_label_color(
                '#abcdef', True, (11, 21, 14, 21+height), image, (10, 20)))

    def test_large_empty_emoji_mask_has_no_python_pixel_loop(self):
        image = Image.new('RGBA', (1600, 900), (20, 140, 230, 255))
        mask = Image.new('L', image.size)
        with mock.patch.object(Image.Image, 'getpixel', side_effect=AssertionError('pixel scan')):
            self.assertEqual('#aabbcc', app.emojimax_solution_label_color(
                '#aabbcc', True, (0, 0, 1600, 900), image, (0, 0), mask))

    def test_large_padding_reads_only_the_selected_pixel(self):
        image = Image.new('RGBA', (1600, 900), (20, 140, 230, 255))
        mask = Image.new('L', image.size)
        ImageDraw.Draw(mask).rectangle((1500, 0, 1599, 899), fill=255)
        original = Image.Image.getpixel
        calls = []
        def counted(im, xy):
            calls.append(xy)
            return original(im, xy)
        with mock.patch.object(Image.Image, 'getpixel', counted):
            self.assertEqual('#148ce6', app.emojimax_solution_label_color(
                '#aabbcc', True, (0, 0, 1600, 900), image, (0, 0), mask))
        self.assertEqual([(1500, 449)], calls)

    def test_fixed_or_missing_source_does_no_image_work(self):
        image = mock.Mock()
        self.assertEqual('#aabbcc', app.emojimax_solution_label_color('#aabbcc', False, None, image))
        self.assertEqual('#f4f8ff', app.emojimax_solution_label_color('invalid', True, None))
        self.assertEqual([], image.mock_calls)


class ArtworkSchedulingTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.pending = {}
        self.serial = 0
        def after(delay, callback):
            self.serial += 1
            token = f'tick-{self.serial}'
            self.pending[token] = callback
            self.events.append(('after', delay))
            return token
        def cancel(token):
            self.events.append(('cancel', token))
            self.pending.pop(token, None)
        self.state = dict(lyric='New lyric now', lyrics_mode=3)
        self.configurator = mock.Mock(is_set=lambda: False)
        self.ns = dict(vars(app), state=self.state, contextlib=contextlib,
            root=SimpleNamespace(after=after, after_cancel=cancel),
            self=SimpleNamespace(_color_configurator_active=self.configurator),
            artwork_karaoke_color_mode_name=lambda: 'lava-lamp',
            karaoke_timed_emphasis_enabled=lambda *args: False,
            animate_artwork_lyric_colors=mock.Mock(),
            lyrics_mode_includes_artwork=lambda _: True,
            artwork_karaoke_palette_index=lambda: 0,
            karaoke_color_mode_index=lambda _: 0,
            karaoke_speed=lambda *args: 1.0,
            karaoke_timing_type=lambda *args: 'line',
            _artwork_native_fast_path_allowed=lambda *args: True)
        functions(self.ns, 'artwork_lyric_animation_interval_ms',
                  'ensure_artwork_lyric_color_animation', 'draw_artwork_lyric_overlay')
        def draw(*args):
            self.events.append(('draw', args[2]))
            self.state.update(artwork_lyric_native_items=[1], artwork_lyric_native_mode='lava-lamp')
            self.ns['ensure_artwork_lyric_color_animation']()
        self.ns['_draw_native_artwork_lyric'] = draw

    def test_new_cue_draws_immediately_then_schedules_only_one_recolor(self):
        for lyric in ('first', 'second', 'third'):
            self.state['lyric'] = lyric
            self.ns['draw_artwork_lyric_overlay'](1920, 1080)
            self.assertEqual(1, len(self.pending))
            self.assertEqual(('draw', lyric), self.events[-2])
            self.assertEqual(('after', app.ARTWORK_LYRIC_NATIVE_FAST_PATH_TICK_MS), self.events[-1])
        self.ns['animate_artwork_lyric_colors'].assert_not_called()
        self.assertEqual(2, sum(event[0] == 'cancel' for event in self.events))

    def test_first_recolor_keeps_existing_size_dependent_cadence(self):
        for size, delay in (((200, 200), 90), ((600, 400), 140), ((1000, 600), 220)):
            self.state.update(artwork_lyric_color_after=None,
                              artwork_lyric_plasma_mask=Image.new('L', size))
            self.ns['ensure_artwork_lyric_color_animation']()
            self.assertEqual(('after', delay), self.events[-1])
            count = len(self.events)
            self.ns['ensure_artwork_lyric_color_animation']()
            self.assertEqual(count, len(self.events))

    def test_blank_or_disabled_cue_cancels_old_timer(self):
        for disabled in (False, True):
            self.ns['draw_artwork_lyric_overlay'](1920, 1080)
            if disabled:
                self.state['artwork_karaoke_enabled'] = False
            else:
                self.state['lyric'] = ''
            self.ns['draw_artwork_lyric_overlay'](1920, 1080)
            self.assertFalse(self.pending)
            self.assertIsNone(self.state['artwork_lyric_color_after'])
            self.state['lyric'] = 'next'

    def test_static_and_configurator_do_not_start_animation(self):
        self.ns['artwork_karaoke_color_mode_name'] = lambda: 'solid'
        self.ns['ensure_artwork_lyric_color_animation']()
        self.assertFalse(self.pending)
        self.ns['karaoke_timed_emphasis_enabled'] = lambda *args: True
        self.ns['ensure_artwork_lyric_color_animation']()
        self.assertTrue(self.pending)
        self.state['artwork_lyric_color_after'] = None
        self.pending.clear()
        self.configurator.is_set = lambda: True
        self.ns['ensure_artwork_lyric_color_animation']()
        self.assertFalse(self.pending)


if __name__ == '__main__':
    unittest.main()
