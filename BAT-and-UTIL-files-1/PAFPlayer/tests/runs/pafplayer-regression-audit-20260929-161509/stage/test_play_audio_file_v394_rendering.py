"""Differential rendering checks and warm-frame benchmark against V393.

Run this file for tests, or pass --benchmark [--profile] for timings. No audio,
terminal output, web requests, registry writes, or music-file access is needed.
"""
import argparse
import cProfile
import importlib.util
import math
from pathlib import Path
import pstats
import random
import statistics
import sys
import time
import unittest


def load_player(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


OLD = load_player('paf_v393_reference', 'play_audio_file_v393_console_visualizer_art_hot_path_VUSIZLIER_AT_30FPS.py')
NEW = load_player('paf_v394_candidate', 'play_audio_file.py')


def fixture(width=32, rows=32, detail=13):
    logical = width * 2
    horizontal = max(2, NEW.art_detail_horizontal_subcells(detail))
    vertical = max(4, NEW.art_detail_vertical_subcells(detail))
    # Deterministic color edges exercise both the DRCS and Unicode branches.
    def color(x, y):
        return ((x * 3 + y * 7) % 256, (x * 5 + y * 11) % 256, (x * 13 + y * 17) % 256)
    grid = tuple(tuple(color(x, y) for x in range(logical)) for y in range(rows))
    micro = tuple(tuple(color(x, y) for x in range(width * horizontal)) for y in range(rows * vertical))
    return dict(
        columns=width, rows=rows, truncate_top_lines=0, granularity=3,
        spectrum_levels=bytes((x * 37) % 256 for x in range(logical)),
        height_override=[0.5 + 0.49 * math.sin(x * .07) for x in range(logical)],
        recent_energy=[((x * 17) % 100) / 100 for x in range(logical)],
        mode=6, color_style=1, processing_style=62, fade_style=1,
        artwork_color_grid=grid, artwork_microtile_color_grid=micro,
        artwork_background_strength=.3, artwork_microtiles_enabled=True,
        artwork_microtile_detail_mode=detail, artwork_bar_microtile_detail_mode=0,
    )


def render(module, options):
    rows, rgb_rows, cells = [], [], []
    result = module.render_drcs_visualizer(
        **options, rows_out=rows, rgb_rows_out=rgb_rows, cell_rows_out=cells,
    )
    return result, rows, rgb_rows, cells


class RenderingEquivalence(unittest.TestCase):
    def assert_same(self, options):
        self.assertEqual(render(OLD, options), render(NEW, options))
        old_rows, new_rows = [], []
        self.assertEqual(
            OLD.render_drcs_visualizer(**options, rows_out=old_rows),
            NEW.render_drcs_visualizer(**options, rows_out=new_rows),
        )
        self.assertEqual(old_rows, new_rows)

    def test_background_modes_resize_crop_and_brightness(self):
        for detail in (0, 1, 2, 3, 7, 8, 9, 10, 11, 12, 13):
            for rows, crop, feedback in ((16, 2, 1.), (32, 0, 1.), (48, 3, .85), (7, 1, 1.17)):
                with self.subTest(detail=detail, rows=rows, feedback=feedback):
                    options = fixture(18, rows, detail)
                    options.update(truncate_top_lines=crop, feedback_brightness=feedback)
                    self.assert_same(options)

    def test_every_fill_boundary_including_rounding_ties(self):
        for rows in (1, 7, 16, 32, 48, 96):
            heights = [-1., 0., 1., 2.]
            for subcell in range(rows * 8):
                height = (subcell + .5) / (rows * 8)
                heights.extend((math.nextafter(height, 0.), height, math.nextafter(height, 1.)))
            options = fixture(12, rows)
            for start in range(0, len(heights), 24):
                batch = heights[start:start + 24]
                batch += [0.] * (24 - len(batch))
                for blank in (0, min(6, rows - 1)):
                    with self.subTest(rows=rows, start=start, blank=blank):
                        options.update(height_override=batch, top_blank_by_logical_column=[blank] * 24)
                        self.assert_same(options)

    def test_fallbacks_and_layer_changes(self):
        rng = random.Random(394)
        options = fixture(24, 32)
        for case in range(60):
            options.update(
                height_override=[rng.uniform(-.1, 1.1) for _ in range(48)],
                top_blank_by_logical_column=[rng.choice((0, 0, 6)) for _ in range(48)],
                granularity=rng.choice((1, 2, 3)),
                processing_style=rng.choice((1, 47, 62, 63)),
                artwork_bar_strength=rng.choice((0., .6)),
                artwork_bar_blend_mode=rng.choice((0, 1, 2)),
                artwork_background_strength=rng.choice((0., .15, .3)),
                artwork_bar_microtiles_enabled=bool(case % 2),
                artwork_bar_microtile_detail_mode=9 if case % 2 else 0,
                force_monochrome=case % 5 == 0,
                feedback_brightness=rng.choice((1., .9, 1.1)),
                rows_only=bool(case % 2),
            )
            with self.subTest(case=case):
                self.assert_same(options)

    def test_artwork_bank_changes_and_cursor_fence_settings(self):
        options = fixture(24, 16)
        options['height_override'] = [0.] * 48
        old_fence, new_fence = OLD.HYBRID_UNICODE_CURSOR_FENCE, NEW.HYBRID_UNICODE_CURSOR_FENCE
        try:
            for fence in (1, 0, 1):
                OLD.HYBRID_UNICODE_CURSOR_FENCE = NEW.HYBRID_UNICODE_CURSOR_FENCE = fence
                for selector in (0, 1, 2):
                    grid = options['artwork_microtile_color_grid']
                    codebook = NEW.adaptive_seamless_drcs_codebook_for_grid(grid, 16, 24)
                    if selector == 1:
                        codebook = tuple(reversed(codebook))
                    elif selector == 2:
                        codebook = None
                    OLD.set_art_detail_drcs_codebook_override(3, codebook)
                    NEW.set_art_detail_drcs_codebook_override(3, codebook)
                    self.assert_same(options)
        finally:
            OLD.set_art_detail_drcs_codebook_override(3, None)
            NEW.set_art_detail_drcs_codebook_override(3, None)
            OLD.HYBRID_UNICODE_CURSOR_FENCE = old_fence
            NEW.HYBRID_UNICODE_CURSOR_FENCE = new_fence


def benchmark(profile=False):
    for width, rows in ((200, 32), (240, 32), (200, 48)):
        options = fixture(width, rows)
        options.update(rows_only=True)
        frames = [
            [.5 + .49 * math.sin(x * .07 + frame * .06) for x in range(width * 2)]
            for frame in range(60)
        ]
        timings = {}
        for label, module in (('V393', OLD), ('candidate', NEW)):
            for heights in frames[:8]:
                module.render_drcs_visualizer(**dict(options, height_override=heights), rows_out=[])
            durations = []
            for heights in frames:
                start = time.perf_counter()
                module.render_drcs_visualizer(**dict(options, height_override=heights), rows_out=[])
                durations.append((time.perf_counter() - start) * 1000)
            timings[label] = statistics.median(durations)
            print(f'{width}x{rows} {label}: median={timings[label]:.2f} ms, p95={sorted(durations)[56]:.2f} ms')
        print(f'  generation speedup: {timings["V393"] / timings["candidate"]:.2f}x')
    if profile:
        options = fixture(200, 32)
        for _ in range(3):
            NEW.render_drcs_visualizer(**options)
        profiler = cProfile.Profile()
        profiler.enable()
        for _ in range(10):
            NEW.render_drcs_visualizer(**options)
        profiler.disable()
        pstats.Stats(profiler).sort_stats('cumtime').print_stats(18)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', action='store_true')
    parser.add_argument('--profile', action='store_true')
    args = parser.parse_args()
    if args.benchmark:
        benchmark(args.profile)
    else:
        unittest.main(argv=[sys.argv[0]])
