"""Exact bar-art rendering comparisons and moving-frame performance checks.

Run with -B to avoid changing bytecode caches. --benchmark includes full-frame
ANSI generation; --profile profiles moving colors after warming the artwork.
These checks do not play audio, write settings, or paint a real terminal.
"""
from __future__ import annotations

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
from unittest import mock


def load_player(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


OLD = load_player("paf_v400_reference", "play_audio_file_v400_help_output_endpoint_details.py")
NEW = load_player("paf_v401_candidate", "play_audio_file.py")


def fixture(width=200, rows=32, detail=9):
    horizontal = max(2, NEW.art_detail_horizontal_subcells(detail))
    vertical = max(4, NEW.art_detail_vertical_subcells(detail))

    def color(x, y):
        return ((x * 3 + y * 7) % 256, (x * 5 + y * 11) % 256, (x * 13 + y * 17) % 256)

    return dict(
        columns=width, rows=rows, truncate_top_lines=0, granularity=3,
        spectrum_levels=bytes((x * 37) % 256 for x in range(width * 2)),
        height_override=[0.5 + 0.49 * math.sin(x * .07) for x in range(width * 2)],
        recent_energy=[((x * 17) % 100) / 100 for x in range(width * 2)],
        mode=6, color_style=1, processing_style=62, fade_style=1,
        artwork_color_grid=tuple(tuple(color(x, y) for x in range(width * 2)) for y in range(rows)),
        artwork_microtile_color_grid=tuple(
            tuple(color(x, y) for x in range(width * horizontal)) for y in range(rows * vertical)
        ),
        artwork_bar_strength=1.0, artwork_bar_blend_mode=1,
        artwork_background_strength=.3, artwork_microtiles_enabled=True,
        artwork_bar_microtiles_enabled=True,
        artwork_microtile_detail_mode=detail, artwork_bar_microtile_detail_mode=detail,
    )


def render(module, options, captures=False):
    rows, rgb, cells = [], [], []
    output = module.render_drcs_visualizer(
        **options, rows_out=rows,
        rgb_rows_out=rgb if captures else None, cell_rows_out=cells if captures else None,
    )
    return output, rows, rgb, cells


class BatchedBarArtwork(unittest.TestCase):
    def test_rgb_arithmetic_matches_scalar(self):
        if NEW._visualizer_numpy() is None:
            self.skipTest("NumPy is optional and not installed")
        rng = random.Random(401)
        rgb = lambda: tuple(rng.randrange(256) for _ in range(3))
        bases = [(0, 0, 0), (255, 255, 255), (1, 1, 0), (127, 128, 129)] + [rgb() for _ in range(80)]
        grid = tuple(tuple((rgb(), rgb(), "A") for _ in bases) for _ in range(4))
        for feedback in (.75, .9, 1.0, 1.00005, 1.13, 1.25):
            for mode in (0, 1, 2):
                for step in (0, 1, 5, 50, 499, 500, 501, 700, 1000):
                    with self.subTest(feedback=feedback, mode=mode, step=step):
                        actual = NEW._visualizer_bar_art_colors(grid, bases, step, mode, feedback)
                        expected = []
                        for row in grid:
                            cells = []
                            for base, cell in zip(bases, row):
                                colors = []
                                for art in cell[:2]:
                                    if abs(feedback - 1.0) >= .0001:
                                        art = tuple(max(0, min(255, round(c * feedback))) for c in art)
                                    colors.append(list(OLD._visualizer_blend_bar_art_cached(*base, *art, step, mode)))
                                cells.append(colors)
                            expected.append(cells)
                        expected = [bytes(c for cell in row for rgb in cell for c in rgb) for row in expected]
                        self.assertEqual(expected, actual)
        self.assertLessEqual(len(NEW._VISUALIZER_BAR_ART_ARRAY_CACHE), 4)

    def test_full_output_and_captures_match(self):
        rng = random.Random(401)
        for detail in (1, 2, 3, 7, 8, 9, 10, 11, 12, 13):
            for mode in (0, 1, 2):
                options = fixture(18, rng.choice((7, 16, 32, 48)), detail)
                options.update(
                    artwork_bar_blend_mode=mode,
                    artwork_bar_strength=rng.choice((.005, .05, .5, .7, 1.0)),
                    feedback_brightness=rng.choice((.85, 1.0, 1.15)),
                    height_override=[rng.uniform(-.1, 1.1) for _ in range(36)],
                    top_blank_by_logical_column=[rng.choice((0, 0, 6)) for _ in range(36)],
                    truncate_top_lines=2,
                )
                for captures in (False, True):
                    with self.subTest(detail=detail, mode=mode, captures=captures):
                        self.assertEqual(render(OLD, options, captures), render(NEW, options, captures))

    def test_fallbacks_and_layer_changes(self):
        options = fixture(18, 24)
        with mock.patch.object(NEW, "_visualizer_numpy", return_value=None):
            self.assertEqual(render(OLD, options), render(NEW, options))
        for changes in (
            dict(processing_style=1), dict(processing_style=58), dict(force_monochrome=True),
            dict(granularity=1), dict(granularity=2), dict(artwork_bar_microtiles_enabled=False),
            dict(artwork_microtiles_enabled=False), dict(artwork_bar_strength=0),
            dict(artwork_background_strength=0), dict(rows_only=True), dict(semantic_cells_only=True),
        ):
            with self.subTest(changes=changes):
                self.assertEqual(render(OLD, dict(options, **changes), True), render(NEW, dict(options, **changes), True))

    def test_warm_full_cells_do_not_use_scalar_blends(self):
        if NEW._visualizer_numpy() is None:
            self.skipTest("NumPy is optional and not installed")
        options = fixture(32, 32)
        options["height_override"] = [1.] * 64
        render(NEW, options)
        with mock.patch.object(NEW, "_visualizer_blend_bar_art_cached", side_effect=AssertionError("scalar blend on full cell")):
            self.assertEqual(render(OLD, options), render(NEW, options))

    def test_edge_blend_rounding_resize_and_crop(self):
        for rows, crop in ((7, 0), (24, 2), (32, 0)):
            options = fixture(12, rows - crop)
            options.update(rows=rows, truncate_top_lines=crop)
            for microtiles in (False, True):
                for mode in (0, 1, 2):
                    for strength in (.0004, .0006, .0505, 1 / 3, .5, .9995):
                        options.update(
                            artwork_bar_blend_mode=mode, artwork_bar_strength=strength,
                            artwork_bar_microtiles_enabled=microtiles,
                            feedback_brightness=.85 if mode == 0 else 1.15,
                            top_blank_by_logical_column=[0, 6] * 12,
                            height_override=[(i + .5) / 24 for i in range(24)],
                        )
                        with self.subTest(rows=rows, crop=crop, mode=mode, strength=strength, microtiles=microtiles):
                            self.assertEqual(render(OLD, options, True), render(NEW, options, True))

    def test_equal_colors_at_full_empty_and_partial_run_boundaries(self):
        for color in ((0, 0, 0), (128, 128, 128), (255, 255, 255)):
            for rows in (7, 32):
                options = fixture(12, rows, 1)
                options.update(
                    artwork_color_grid=tuple(tuple(color for _ in row) for row in options["artwork_color_grid"]),
                    artwork_microtile_color_grid=tuple(tuple(color for _ in row) for row in options["artwork_microtile_color_grid"]),
                    artwork_bar_blend_mode=0, artwork_background_strength=1.,
                    height_override=[0., 0., 1., 1., .5, .5, 1., 1.] * 3,
                )
                self.assertEqual(render(OLD, options, True), render(NEW, options, True))

    def test_artwork_bar_fill_rounding_ties(self):
        for rows in (1, 7, 24, 48):
            options = fixture(12, rows, 1)
            heights = [-1., 0., 1., 2.]
            for subcell in range(rows * 8):
                height = (subcell + .5) / (rows * 8)
                heights.extend((math.nextafter(height, 0.), height, math.nextafter(height, 1.)))
            for start in range(0, len(heights), 24):
                batch = heights[start:start + 24]
                options["height_override"] = batch + [0.] * (24 - len(batch))
                self.assertEqual(render(OLD, options, True), render(NEW, options, True))


def moving_frames(width, count=72):
    return [dict(
        height_override=[.5 + .49 * math.sin(x * .07 + frame * .06) for x in range(width * 2)],
        recent_energy=[.5 + .49 * math.sin(x * .041 + frame * .023) for x in range(width * 2)],
    ) for frame in range(count)]


def timed(module, options, frames):
    for frame in frames[:8]:
        module.render_drcs_visualizer(**dict(options, **frame), rows_out=[])
    durations = []
    for frame in frames:
        started = time.perf_counter()
        module.render_drcs_visualizer(**dict(options, **frame), rows_out=[])
        durations.append((time.perf_counter() - started) * 1000)
    return durations


def benchmark(profile=False):
    print("Full-frame ANSI generation; moving heights AND energies; no terminal I/O", flush=True)
    for width, rows, detail in ((200, 32, 9), (240, 32, 9), (200, 48, 9), (200, 32, 13)):
        options = fixture(width, rows, detail)
        frames = moving_frames(width)
        old = timed(OLD, options, frames)
        new = timed(NEW, options, frames)
        print(
            f"{width}x{rows} detail {detail}: V400 {statistics.median(old):.2f} ms; "
            f"V401 {statistics.median(new):.2f} ms; p95 {sorted(new)[math.ceil(len(new)*.95)-1]:.2f} ms; "
            f"speedup {statistics.median(old)/statistics.median(new):.2f}x", flush=True,
        )
    if profile:
        options = fixture()
        frames = moving_frames(200, 24)
        timed(NEW, options, frames[:8])
        profiler = cProfile.Profile()
        profiler.enable()
        for frame in frames:
            NEW.render_drcs_visualizer(**dict(options, **frame), rows_out=[])
        profiler.disable()
        pstats.Stats(profiler).sort_stats("cumtime").print_stats(20)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    if args.benchmark:
        benchmark(args.profile)
    else:
        unittest.main(argv=[sys.argv[0]])
