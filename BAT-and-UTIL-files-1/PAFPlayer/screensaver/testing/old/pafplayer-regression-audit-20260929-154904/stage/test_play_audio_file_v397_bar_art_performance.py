"""Differential and performance checks for the V397 bar-art fast path."""

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


def load_player(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


OLD = load_player("paf_v396_bar_art_reference", "play_audio_file_v396_cursive_fix_experimental_color.py")
NEW = load_player("paf_v397_bar_art_candidate", "play_audio_file.py")


def fixture(width: int = 200, rows: int = 32, detail: int = 13) -> dict[str, object]:
    logical = width * 2
    horizontal = max(2, NEW.art_detail_horizontal_subcells(detail))
    vertical = max(4, NEW.art_detail_vertical_subcells(detail))

    def color(x: int, y: int) -> tuple[int, int, int]:
        return (
            (x * 3 + y * 7) % 256,
            (x * 5 + y * 11) % 256,
            (x * 13 + y * 17) % 256,
        )

    grid = tuple(tuple(color(x, y) for x in range(logical)) for y in range(rows))
    micro = tuple(
        tuple(color(x, y) for x in range(width * horizontal))
        for y in range(rows * vertical)
    )
    return {
        "columns": width,
        "rows": rows,
        "truncate_top_lines": 0,
        "granularity": 3,
        "spectrum_levels": bytes((x * 37) % 256 for x in range(logical)),
        "height_override": [0.5 + 0.49 * math.sin(x * 0.07) for x in range(logical)],
        "recent_energy": [((x * 17) % 100) / 100 for x in range(logical)],
        "mode": 6,
        "color_style": 1,
        "processing_style": 62,
        "fade_style": 1,
        "artwork_color_grid": grid,
        "artwork_microtile_color_grid": micro,
        "artwork_bar_strength": 0.7,
        "artwork_bar_blend_mode": 1,
        "artwork_background_strength": 0.3,
        "artwork_microtiles_enabled": True,
        "artwork_bar_microtiles_enabled": True,
        "artwork_microtile_detail_mode": detail,
        "artwork_bar_microtile_detail_mode": detail,
        "rows_only": True,
    }


def render(module, options: dict[str, object], *, captures: bool = False):
    rows: list[str] = []
    if not captures:
        return module.render_drcs_visualizer(**options, rows_out=rows), rows
    rgb: list[list[tuple[int, int, int] | None]] = []
    cells: list[list[tuple[tuple[int, int, int], str]]] = []
    output = module.render_drcs_visualizer(
        **options, rows_out=rows, rgb_rows_out=rgb, cell_rows_out=cells
    )
    return output, rows, rgb, cells


class BarArtworkEquivalence(unittest.TestCase):
    def assert_same(self, options: dict[str, object]) -> None:
        self.assertEqual(render(OLD, options), render(NEW, options))
        self.assertEqual(render(OLD, options, captures=True), render(NEW, options, captures=True))

    def test_bar_art_modes_and_geometry(self) -> None:
        rng = random.Random(397)
        for rows in (7, 16, 32, 48):
            options = fixture(18, rows)
            for mode in (0, 1, 2):
                for microtiles in (False, True):
                    options.update(
                        artwork_bar_blend_mode=mode,
                        artwork_bar_microtiles_enabled=microtiles,
                        artwork_bar_microtile_detail_mode=13 if microtiles else 0,
                        feedback_brightness=rng.choice((0.85, 1.0, 1.15)),
                        truncate_top_lines=min(2, rows - 1),
                        top_blank_by_logical_column=[rng.choice((0, 0, min(6, rows - 1))) for _ in range(36)],
                        height_override=[rng.uniform(-0.1, 1.1) for _ in range(36)],
                    )
                    with self.subTest(rows=rows, mode=mode, microtiles=microtiles):
                        self.assert_same(options)


def timed(module, options: dict[str, object], frames: list[list[float]]) -> list[float]:
    for heights in frames[:8]:
        module.render_drcs_visualizer(**dict(options, height_override=heights), rows_out=[])
    durations = []
    for heights in frames:
        started = time.perf_counter()
        module.render_drcs_visualizer(**dict(options, height_override=heights), rows_out=[])
        durations.append((time.perf_counter() - started) * 1000.0)
    return durations


def benchmark(profile: bool = False) -> None:
    for width, rows in ((200, 32), (240, 32), (200, 48)):
        options = fixture(width, rows, NEW.ART_MICROTILE_DETAIL_MODE_DEFAULT)
        frames = [
            [0.5 + 0.49 * math.sin(x * 0.07 + frame * 0.06) for x in range(width * 2)]
            for frame in range(60)
        ]
        old = timed(OLD, options, frames)
        new = timed(NEW, options, frames)
        old_median = statistics.median(old)
        new_median = statistics.median(new)
        print(
            f"{width}x{rows}: V396 {old_median:.2f} ms; candidate {new_median:.2f} ms; "
            f"speedup {old_median / new_median:.2f}x; candidate ceiling {1000.0 / new_median:.1f} FPS"
        )
    if profile:
        options = fixture(200, 32, NEW.ART_MICROTILE_DETAIL_MODE_DEFAULT)
        profiler = cProfile.Profile()
        profiler.enable()
        for _ in range(20):
            NEW.render_drcs_visualizer(**options, rows_out=[])
        profiler.disable()
        pstats.Stats(profiler).sort_stats("cumtime").print_stats(24)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    if args.benchmark:
        benchmark(args.profile)
    else:
        unittest.main(argv=[sys.argv[0]])
