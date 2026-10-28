r"""COPY of PAFPlayer's Twin DRCS artwork definitions; ICGF fallback only.

Original: C:\BAT\PAFPlayer\PAFPlayer.py, copied 2026-10-27.
Original SHA-256: fc6e7301f3aef7515be171bdccf62f2ed30a11581f24280b372e90f90de49e97
The runtime prefers installed sibling PAFPlayer. These selected definitions and
their graphics-only dependencies are preserved verbatim with original line ranges.
No PAFPlayer startup, playback, registry writes or application initialization code
is included. Keep this explicit copy attribution with future edits.
"""
from __future__ import annotations
from functools import lru_cache
import io, json, math, os, re, shutil, subprocess, threading, time
from pathlib import Path

# COPIED FROM PAFPlayer: PROGRAM_VERSION; original lines 606-606.
PROGRAM_VERSION                = 'V628'

# COPIED FROM PAFPlayer: PAFPLAYER_REGISTRY_ROOT; original lines 1041-1041.
PAFPLAYER_REGISTRY_ROOT = r"Software\ClaireCJS\PAFPlayer"

# COPIED FROM PAFPlayer: PAFPLAYER_LEGACY_REGISTRY_ROOT; original lines 1042-1042.
PAFPLAYER_LEGACY_REGISTRY_ROOT = r"Software\ClaireCJS\play_audio_file"

# COPIED FROM PAFPlayer: HYBRID_UNICODE_CURSOR_FENCE; original lines 1789-1789.
HYBRID_UNICODE_CURSOR_FENCE      = 1  # V381 EXP: after every native Unicode artwork cell, explicitly restore the cursor to the next expected terminal column. Windows Terminal occasionally advances mixed Unicode+DRCS mosaic glyphs inconsistently; this confines any bad advance to that one cell instead of shifting the remainder of the artwork row.

# COPIED FROM PAFPlayer: ARTWORK_SEAM_STRATEGY; original lines 2010-2010.
ARTWORK_SEAM_STRATEGY = 5

# COPIED FROM PAFPlayer: ART_MICROTILE_DETAIL_MODE_GEOMETRIES; original lines 2041-2056.
ART_MICROTILE_DETAIL_MODE_GEOMETRIES = (
    (1, 1),  # 0: single-character color only; no within-cell mask
    (2, 2),  # 1: quadrant / DRCS
    (2, 3),  # 2: sextant / DRCS
    (2, 4),  # 3: octant / DRCS approximation bank
    (3, 3),  # 4: 9-subcell DRCS approximation bank
    (2, 5),  # 5: 10-subcell DRCS approximation bank
    (3, 4),  # 6: 12-subcell DRCS approximation bank
    (2, 2),  # 7: Unicode + DRCS quadrant
    (2, 3),  # 8: Unicode + DRCS sextant
    (2, 4),  # 9: Unicode + DRCS octant
    (3, 3),  # 10: adaptive exact 3×3, exact 2×4 fallback
    (2, 5),  # 11: adaptive exact 2×5, exact 2×4 fallback
    (3, 4),  # 12: adaptive exact 3×4, exact 2×4 fallback
    (2, 4),  # 13: artwork-adaptive seamless 2×4 hybrid
)

# COPIED FROM PAFPlayer: ART_MICROTILE_DETAIL_HYBRID_BASE_MODE; original lines 2057-2057.
ART_MICROTILE_DETAIL_HYBRID_BASE_MODE = {7: 1, 8: 2, 9: 3}

# COPIED FROM PAFPlayer: ART_MICROTILE_DETAIL_ADAPTIVE_EXACT_BASE_MODE; original lines 2058-2058.
ART_MICROTILE_DETAIL_ADAPTIVE_EXACT_BASE_MODE = {10: 4, 11: 5, 12: 6}

# COPIED FROM PAFPlayer: ART_MICROTILE_DETAIL_SEAMLESS_BASE_MODE; original lines 2059-2059.
ART_MICROTILE_DETAIL_SEAMLESS_BASE_MODE = {13: 3}

# COPIED FROM PAFPlayer: ART_MICROTILE_DETAIL_MODE_NAMES; original lines 2060-2075.
ART_MICROTILE_DETAIL_MODE_NAMES = (
    "Single-character detail (1 subcell — 100% exact output — Unicode mosaics OFF; color cell only)",
    "2×2 quadrant detail (4 subcells — 100% exact — Unicode mosaics OFF; DRCS only)",
    "2×3 sextant detail (6 subcells — 100% exact — Unicode mosaics OFF; DRCS only)",
    "2×4 octant detail (8 subcells — 43% exact masks — Unicode mosaics OFF; DRCS only)",
    "3×3 mosaic detail (9 subcells — 21% exact masks — Unicode mosaics OFF; DRCS only)",
    "2×5 mosaic detail (10 subcells — 11% exact masks — Unicode mosaics OFF; DRCS only)",
    "3×4 mosaic detail (12 subcells — 2.7% exact masks — Unicode mosaics OFF; DRCS only)",
    "2×2 quadrant hybrid (4 subcells — 100% exact — Unicode mosaics ON; Unicode+DRCS)",
    "2×3 sextant hybrid (6 subcells — 100% exact — Unicode mosaics ON; Unicode+DRCS)",
    "2×4 octant hybrid (8 subcells — 100% exact — Unicode mosaics ON; Unicode+DRCS)",
    "3×3 adaptive exact hybrid (up to 9 subcells — 100% exact output — Unicode mosaics ON; exact DRCS or exact 2×4 fallback)",
    "2×5 adaptive exact hybrid (up to 10 subcells — 100% exact output — Unicode mosaics ON; exact DRCS or exact 2×4 fallback)",
    "3×4 adaptive exact hybrid (up to 12 subcells — 100% exact output — Unicode mosaics ON; exact DRCS or exact 2×4 fallback)",
    "2×4 adaptive seamless hybrid (8 subcells — 100% exact — Unicode mosaics ON; used only when needed after artwork-adaptive DRCS)",
)

# COPIED FROM PAFPlayer: ART_MICROTILE_DETAIL_MODE_DEFAULT; original lines 2080-2080.
ART_MICROTILE_DETAIL_MODE_DEFAULT = 9  # 2×4 octant hybrid, 100% exact

# COPIED FROM PAFPlayer: terminal_cell_pixel_size_nonintrusive; original lines 19927-19976.
def terminal_cell_pixel_size_nonintrusive(*, use_win32_font: bool = True) -> tuple[int, int]:
    """Return terminal character-cell pixels without issuing VT window queries.

    Earlier builds repeatedly called claire_terminal_geometry.query_terminal_geometry(),
    which sends CSI 14t/16t/18t terminal-window queries and temporarily changes console
    input mode.  That is clever, but on some Windows Terminal/ConPTY configurations it
    can disturb another application's fullscreen/focus state.  The player only needs an
    approximate font-cell ratio for SIXEL sizing, so V27 uses the passive Win32 font API
    (or a conservative fallback) and never sends terminal-window-control queries during
    playback.
    """
    now = time.monotonic()
    cached = getattr(terminal_cell_pixel_size_nonintrusive, "_cached", None)
    cached_at = getattr(terminal_cell_pixel_size_nonintrusive, "_cached_at", -60.0)
    if cached is not None and now - cached_at < 30.0:
        return cached
    result = (10, 20)
    if os.name == "nt" and use_win32_font:
        try:
            import ctypes
            from ctypes import wintypes

            class COORD(ctypes.Structure):
                _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

            class CONSOLE_FONT_INFOEX(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.ULONG),
                    ("nFont", wintypes.DWORD),
                    ("dwFontSize", COORD),
                    ("FontFamily", wintypes.UINT),
                    ("FontWeight", wintypes.UINT),
                    ("FaceName", wintypes.WCHAR * 32),
                ]

            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            info = CONSOLE_FONT_INFOEX()
            info.cbSize = ctypes.sizeof(info)
            if ctypes.windll.kernel32.GetCurrentConsoleFontEx(
                handle, False, ctypes.byref(info)
            ):
                width = int(info.dwFontSize.X)
                height = int(info.dwFontSize.Y)
                if width > 0 and height > 0:
                    result = (width, height)
        except (AttributeError, OSError, TypeError, ValueError):
            pass
    terminal_cell_pixel_size_nonintrusive._cached = result
    terminal_cell_pixel_size_nonintrusive._cached_at = now
    return result

# COPIED FROM PAFPlayer: ANSI_CSI_RE; original lines 20023-20026.
ANSI_CSI_RE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[0-9]|[()][ -~]|\]8;;.*?(?:\x07|\x1b\\))",
    re.DOTALL,
)

# COPIED FROM PAFPlayer: _drcs_pattern; original lines 29876-29890.
def _drcs_pattern(rows: tuple[str, ...]) -> str:
    """Encode a small monochrome bitmap as the sixel payload of one DRCS glyph."""
    width = len(rows[0])
    bands: list[str] = []
    for top in range(0, len(rows), 6):
        columns: list[str] = []
        for column in range(width):
            bits = sum(
                1 << bit
                for bit in range(6)
                if top + bit < len(rows) and rows[top + bit][column] == "#"
            )
            columns.append(chr(0x3F + bits))
        bands.append("".join(columns))
    return "/".join(bands)

# COPIED FROM PAFPlayer: define_volume_drcs; original lines 29893-29971.
def define_volume_drcs() -> str:
    """Define a speaker and two wave glyphs in unused |, }, and ~ slots."""
    body = (
        "..........",
        "..........",
        "......##..",
        ".....###..",
        "....####..",
        "...#####..",
        "..######..",
        "########..",
        "########..",
        "########..",
        "########..",
        "########..",
        "########..",
        "..######..",
        "...#####..",
        "....####..",
        ".....###..",
        "......##..",
        "..........",
        "..........",
    )
    up_waves = (
        "..........",
        "..........",
        "..##......",
        "....##....",
        ".....##...",
        ".##...##..",
        "...##..##.",
        "....##..##",
        ".....#..##",
        ".....#...#",
        ".....#...#",
        ".....#..##",
        "....##..##",
        "...##..##.",
        ".##...##..",
        ".....##...",
        "....##....",
        "..##......",
        "..........",
        "..........",
    )
    down_waves = (
        "..........",
        "..........",
        "..........",
        "..........",
        "..........",
        "..##......",
        "....##....",
        ".....##...",
        "......##..",
        ".......#..",
        ".......#..",
        "......##..",
        ".....##...",
        "....##....",
        "..##......",
        "..........",
        "..........",
        "..........",
        "..........",
        "..........",
    )
    # Pcn 92 maps to |; Pe 1 only reloads these three slots.  The unregistered
    # "space @" charset is selected only while the player emits its icon.
    return (
        "\033P0;92;1;10;0;2;20;0{ @"
        + _drcs_pattern(body)
        + ";"
        + _drcs_pattern(up_waves)
        + ";"
        + _drcs_pattern(down_waves)
        + "\033\\"
    )

# COPIED FROM PAFPlayer: define_twin_visualizer_drcs_patterns; original lines 30006-30027.
def define_twin_visualizer_drcs_patterns(level_count: int = 9) -> list[str]:
    """Return left/right half-width DRCS combinations for granularity mode 3.

    The historical player font uses 9 levels per half (81 glyphs). Dense-art
    mode deliberately uses 8 levels per half (64 glyphs), freeing enough of the
    same 94-character DRCS set for cell-safe 2×4 artwork masks.  The visual bar
    loses only one intermediate height while avoiding Unicode font fallback.
    """
    levels = max(2, min(9, int(level_count)))
    denominator = levels - 1
    patterns: list[str] = []
    for left in range(levels):
        left_rows = round(left * 20 / denominator)
        for right in range(levels):
            right_rows = round(right * 20 / denominator)
            rows = []
            for row in range(20):
                left_fill = "#####" if row >= 20 - left_rows else "....."
                right_fill = "#####" if row >= 20 - right_rows else "....."
                rows.append(left_fill + right_fill)
            patterns.append(_drcs_pattern(tuple(rows)))
    return patterns

# COPIED FROM PAFPlayer: ART_DETAIL_DRCS_TWIN_LEVELS_BY_MODE; original lines 30035-30041.
ART_DETAIL_DRCS_TWIN_LEVELS_BY_MODE = {
    2: 7,  # 49 twin bars + 32 exact sextant masks + 10 spare + 3 volume
    3: 6,  # 36 twin bars + 55 octant masks + 3 volume
    4: 6,
    5: 6,
    6: 6,
}

# COPIED FROM PAFPlayer: ART_DETAIL_DRCS_ART_SLOTS_BY_MODE; original lines 30042-30045.
ART_DETAIL_DRCS_ART_SLOTS_BY_MODE = {
    mode: 94 - 3 - levels * levels
    for mode, levels in ART_DETAIL_DRCS_TWIN_LEVELS_BY_MODE.items()
}

# COPIED FROM PAFPlayer: art_detail_is_hybrid; original lines 30048-30050.
def art_detail_is_hybrid(mode: int) -> bool:
    """Return whether a selector is one of the universal exact Unicode+DRCS hybrids."""
    return int(mode) in ART_MICROTILE_DETAIL_HYBRID_BASE_MODE

# COPIED FROM PAFPlayer: art_detail_is_adaptive_exact; original lines 30053-30055.
def art_detail_is_adaptive_exact(mode: int) -> bool:
    """Return whether a selector uses exact high-res DRCS with exact 2×4 fallback."""
    return int(mode) in ART_MICROTILE_DETAIL_ADAPTIVE_EXACT_BASE_MODE

# COPIED FROM PAFPlayer: art_detail_is_seamless_adaptive; original lines 30058-30060.
def art_detail_is_seamless_adaptive(mode: int) -> bool:
    """Return whether a selector dynamically spends DRCS slots on this artwork."""
    return int(mode) in ART_MICROTILE_DETAIL_SEAMLESS_BASE_MODE

# COPIED FROM PAFPlayer: art_detail_uses_unicode_glyphs; original lines 30063-30065.
def art_detail_uses_unicode_glyphs(mode: int) -> bool:
    """Return whether a selector is allowed to emit native Unicode mosaic glyphs."""
    return art_detail_is_hybrid(mode) or art_detail_is_adaptive_exact(mode) or art_detail_is_seamless_adaptive(mode)

# COPIED FROM PAFPlayer: art_detail_base_mode; original lines 30068-30075.
def art_detail_base_mode(mode: int) -> int:
    """Return the underlying geometry mode for hybrid/adaptive selectors."""
    value = int(mode)
    if value in ART_MICROTILE_DETAIL_HYBRID_BASE_MODE:
        return ART_MICROTILE_DETAIL_HYBRID_BASE_MODE[value]
    if value in ART_MICROTILE_DETAIL_ADAPTIVE_EXACT_BASE_MODE:
        return ART_MICROTILE_DETAIL_ADAPTIVE_EXACT_BASE_MODE[value]
    return ART_MICROTILE_DETAIL_SEAMLESS_BASE_MODE.get(value, value)

# COPIED FROM PAFPlayer: art_detail_drcs_layout_mode; original lines 30078-30081.
def art_detail_drcs_layout_mode(mode: int) -> int:
    """Return which downloadable bank a selector needs, if any."""
    base = art_detail_base_mode(mode)
    return base if base >= 2 else 0

# COPIED FROM PAFPlayer: choose_art_detail_drcs_layout; original lines 30084-30087.
def choose_art_detail_drcs_layout(*modes: int) -> int:
    """Pick the densest required DRCS bank without confusing hybrid IDs with density."""
    candidates = [art_detail_drcs_layout_mode(mode) for mode in modes]
    return max(candidates, default=0)

# COPIED FROM PAFPlayer: _normalize_art_detail_layout_mode; original lines 30090-30102.
def _normalize_art_detail_layout_mode(value: int | bool) -> int:
    """Normalize a requested DRCS bank mode.

    ``True`` is retained as a compatibility spelling for the old V378 dense
    layout and maps to 2×4 (mode 3); ``False`` means the legacy/2×2 bank.
    Hybrid selector IDs normalize to their underlying DRCS geometry.
    """
    if isinstance(value, bool):
        return 3 if value else 0
    mode = art_detail_base_mode(int(value))
    if mode < 2:
        return 0
    return max(2, min(6, mode))

# COPIED FROM PAFPlayer: art_detail_geometry; original lines 30105-30107.
def art_detail_geometry(mode: int) -> tuple[int, int]:
    index = max(0, min(len(ART_MICROTILE_DETAIL_MODE_GEOMETRIES) - 1, int(mode)))
    return ART_MICROTILE_DETAIL_MODE_GEOMETRIES[index]

# COPIED FROM PAFPlayer: art_detail_horizontal_subcells; original lines 30110-30111.
def art_detail_horizontal_subcells(mode: int) -> int:
    return art_detail_geometry(mode)[0]

# COPIED FROM PAFPlayer: art_detail_subcell_count; original lines 30118-30120.
def art_detail_subcell_count(mode: int) -> int:
    columns, rows = art_detail_geometry(mode)
    return columns * rows

# COPIED FROM PAFPlayer: _canonical_art_detail_mask; original lines 30139-30145.
def _canonical_art_detail_mask(mask: int, bits: int) -> tuple[int, bool]:
    full = (1 << max(1, int(bits))) - 1
    value = int(mask) & full
    complement = value ^ full
    if complement < value:
        return complement, True
    return value, False

# COPIED FROM PAFPlayer: _art_detail_mask_edge_complexity; original lines 30148-30158.
def _art_detail_mask_edge_complexity(mask: int, columns: int, rows: int) -> int:
    """Count neighboring subcell transitions; lower values resemble real edges."""
    score = 0
    for row in range(rows):
        for column in range(columns):
            bit = bool(mask & (1 << (row * columns + column)))
            if column + 1 < columns:
                score += bit != bool(mask & (1 << (row * columns + column + 1)))
            if row + 1 < rows:
                score += bit != bool(mask & (1 << ((row + 1) * columns + column)))
    return int(score)

# COPIED FROM PAFPlayer: art_detail_drcs_codebook; original lines 30162-30214.
def art_detail_drcs_codebook(layout_mode: int) -> tuple[int, ...]:
    """Return the geometry-specific canonical masks downloaded for one mode.

    2×3 stores every possible foreground/background-equivalent mask exactly.
    Larger rasters cannot fit every theoretical shape in a 94-character DRCS
    font, so V379 uses an edge-aware k-center codebook: seed it with a few of
    the spatially smoothest masks, then greedily add masks farthest in Hamming
    distance from those already selected. This protects common continuous image
    edges while still covering pathological masks reasonably well.
    """
    mode = _normalize_art_detail_layout_mode(layout_mode)
    if mode <= 1:
        return tuple(range(8))
    columns, rows = art_detail_geometry(mode)
    bits = columns * rows
    slots = ART_DETAIL_DRCS_ART_SLOTS_BY_MODE[mode]
    full = (1 << bits) - 1
    canonical_masks = tuple(sorted({min(mask, mask ^ full) for mask in range(1 << bits)}))
    if len(canonical_masks) <= slots:
        return canonical_masks

    smooth = sorted(
        canonical_masks,
        key=lambda mask: (
            _art_detail_mask_edge_complexity(mask, columns, rows),
            abs(mask.bit_count() - bits / 2.0),
            mask,
        ),
    )
    seed_count = 8 if bits >= 12 else 4
    selected = list(smooth[: min(seed_count, slots)])
    selected_set = set(selected)
    while len(selected) < slots:
        best_mask = None
        best_key = None
        for mask in canonical_masks:
            if mask in selected_set:
                continue
            distance = min((mask ^ chosen).bit_count() for chosen in selected)
            key = (
                distance,
                -_art_detail_mask_edge_complexity(mask, columns, rows),
                -abs(mask.bit_count() - bits / 2.0),
                -mask,
            )
            if best_key is None or key > best_key:
                best_key = key
                best_mask = mask
        if best_mask is None:
            break
        selected.append(best_mask)
        selected_set.add(best_mask)
    return tuple(selected)

# COPIED FROM PAFPlayer: _ART_DETAIL_DRCS_CODEBOOK_OVERRIDES: dict[int, tuple[int, ...]]; original lines 30217-30217.
_ART_DETAIL_DRCS_CODEBOOK_OVERRIDES: dict[int, tuple[int, ...]] = {}

# COPIED FROM PAFPlayer: _ART_DETAIL_DRCS_CHAR_MAP_OVERRIDES: dict[int, dict[int, str]]; original lines 30218-30218.
_ART_DETAIL_DRCS_CHAR_MAP_OVERRIDES: dict[int, dict[int, str]] = {}

# COPIED FROM PAFPlayer: _ART_DETAIL_DRCS_OVERRIDE_GENERATION; original lines 30219-30219.
_ART_DETAIL_DRCS_OVERRIDE_GENERATION = 0

# COPIED FROM PAFPlayer: art_detail_active_drcs_codebook; original lines 30225-30228.
def art_detail_active_drcs_codebook(layout_mode: int) -> tuple[int, ...]:
    """Return the currently downloaded mask vocabulary for one DRCS geometry."""
    mode = _normalize_art_detail_layout_mode(layout_mode)
    return _ART_DETAIL_DRCS_CODEBOOK_OVERRIDES.get(mode, art_detail_drcs_codebook(mode))

# COPIED FROM PAFPlayer: _art_detail_fixed_drcs_char_by_mask; original lines 30232-30239.
def _art_detail_fixed_drcs_char_by_mask(layout_mode: int) -> dict[int, str]:
    mode = _normalize_art_detail_layout_mode(layout_mode)
    levels = ART_DETAIL_DRCS_TWIN_LEVELS_BY_MODE[mode]
    first = 33 + levels * levels
    return {
        mask: chr(first + index)
        for index, mask in enumerate(art_detail_drcs_codebook(mode))
    }

# COPIED FROM PAFPlayer: _art_detail_drcs_char_by_mask; original lines 30242-30245.
def _art_detail_drcs_char_by_mask(layout_mode: int) -> dict[int, str]:
    mode = _normalize_art_detail_layout_mode(layout_mode)
    override = _ART_DETAIL_DRCS_CHAR_MAP_OVERRIDES.get(mode)
    return override if override is not None else _art_detail_fixed_drcs_char_by_mask(mode)

# COPIED FROM PAFPlayer: _resample_art_detail_mask; original lines 30323-30343.
def _resample_art_detail_mask(mask: int, source_mode: int, target_mode: int) -> int:
    """Nearest-neighbor-resample one binary subcell raster into another geometry."""
    source_columns, source_rows = art_detail_geometry(source_mode)
    target_columns, target_rows = art_detail_geometry(target_mode)
    if (source_columns, source_rows) == (target_columns, target_rows):
        return int(mask) & ((1 << (source_columns * source_rows)) - 1)
    result = 0
    for target_row in range(target_rows):
        source_row = min(
            source_rows - 1,
            max(0, int((target_row + 0.5) * source_rows / target_rows)),
        )
        for target_column in range(target_columns):
            source_column = min(
                source_columns - 1,
                max(0, int((target_column + 0.5) * source_columns / target_columns)),
            )
            source_bit = source_row * source_columns + source_column
            if int(mask) & (1 << source_bit):
                result |= 1 << (target_row * target_columns + target_column)
    return result

# COPIED FROM PAFPlayer: dense_art_drcs_char; original lines 30347-30367.
def dense_art_drcs_char(mask: int, source_mode: int = 3, layout_mode: int = 3) -> tuple[str, bool]:
    """Return the nearest fixed-cell DRCS mosaic plus whether FG/BG must swap."""
    layout = _normalize_art_detail_layout_mode(layout_mode)
    if layout == 0:
        # Compatibility fallback; callers should use the exact 2×2 helper.
        canonical = min(int(mask) & 0xF, (int(mask) & 0xF) ^ 0xF)
        return art_microtile_drcs_char(canonical), canonical != (int(mask) & 0xF)
    target_mask = _resample_art_detail_mask(int(mask), int(source_mode), layout)
    bits = art_detail_subcell_count(layout)
    canonical, invert = _canonical_art_detail_mask(target_mask, bits)
    codebook = art_detail_active_drcs_codebook(layout)
    representative = min(
        codebook,
        key=lambda candidate: (
            (canonical ^ candidate).bit_count(),
            _art_detail_mask_edge_complexity(candidate, *art_detail_geometry(layout)),
            abs(canonical.bit_count() - candidate.bit_count()),
            candidate,
        ),
    )
    return _art_detail_drcs_char_by_mask(layout)[representative], invert

# COPIED FROM PAFPlayer: define_dense_art_drcs_patterns; original lines 30370-30387.
def define_dense_art_drcs_patterns(layout_mode: int = 3) -> list[str]:
    """Build geometry-specific fixed-cell artwork glyphs for one DRCS bank."""
    mode = _normalize_art_detail_layout_mode(layout_mode)
    columns, rows = art_detail_geometry(mode)
    x_edges = [round(index * 10 / columns) for index in range(columns + 1)]
    y_edges = [round(index * 20 / rows) for index in range(rows + 1)]
    patterns: list[str] = []
    for mask in art_detail_active_drcs_codebook(mode):
        bitmap = [["." for _column in range(10)] for _row in range(20)]
        for subrow in range(rows):
            for subcolumn in range(columns):
                if not (mask & (1 << (subrow * columns + subcolumn))):
                    continue
                for pixel_row in range(y_edges[subrow], y_edges[subrow + 1]):
                    for pixel_column in range(x_edges[subcolumn], x_edges[subcolumn + 1]):
                        bitmap[pixel_row][pixel_column] = "#"
        patterns.append(_drcs_pattern(tuple("".join(row) for row in bitmap)))
    return patterns

# COPIED FROM PAFPlayer: art_microtile_drcs_char; original lines 30396-30400.
def art_microtile_drcs_char(mask: int) -> str:
    """Map any binary 2×2 mask to one of eight DRCS microtiles in r..y."""
    mask = int(mask) & 0xF
    canonical = min(mask, mask ^ 0xF)
    return chr(ord("r") + canonical)

# COPIED FROM PAFPlayer: define_art_microtile_drcs_patterns; original lines 30403-30417.
def define_art_microtile_drcs_patterns() -> list[str]:
    """Return eight 2×2 quadrant masks for experimental two-color artwork."""
    patterns: list[str] = []
    for mask in range(8):
        bitmap: list[str] = []
        for row in range(20):
            bottom = row >= 10
            pixels: list[str] = []
            for column in range(10):
                right = column >= 5
                bit = (8 if right else 4) if bottom else (2 if right else 1)
                pixels.append("#" if mask & bit else ".")
            bitmap.append("".join(pixels))
        patterns.append(_drcs_pattern(tuple(bitmap)))
    return patterns

# COPIED FROM PAFPlayer: _SEXTANT_MASK_ORDER; original lines 30420-30422.
_SEXTANT_MASK_ORDER = tuple(
    [mask for mask in range(1, 63) if mask not in {21, 42}]
)

# COPIED FROM PAFPlayer: _SEXTANT_CHAR_BY_MASK; original lines 30423-30426.
_SEXTANT_CHAR_BY_MASK = {
    mask: chr(0x1FB00 + index)
    for index, mask in enumerate(_SEXTANT_MASK_ORDER)
}

# COPIED FROM PAFPlayer: art_detail_vertical_subcells; original lines 30430-30432.
def art_detail_vertical_subcells(mode: int) -> int:
    """Return vertical sample count for one artwork-detail mode."""
    return art_detail_geometry(mode)[1]

# COPIED FROM PAFPlayer: _QUADRANT_UNICODE_BY_MASK; original lines 30435-30440.
_QUADRANT_UNICODE_BY_MASK = {
    0x0: " ", 0x1: "▘", 0x2: "▝", 0x3: "▀",
    0x4: "▖", 0x5: "▌", 0x6: "▞", 0x7: "▛",
    0x8: "▗", 0x9: "▚", 0xA: "▐", 0xB: "▜",
    0xC: "▄", 0xD: "▙", 0xE: "▟", 0xF: "█",
}

# COPIED FROM PAFPlayer: art_quadrant_unicode_char; original lines 30443-30445.
def art_quadrant_unicode_char(mask: int) -> tuple[str, bool]:
    """Return the exact native Unicode 2×2 block glyph for one row-major mask."""
    return _QUADRANT_UNICODE_BY_MASK[int(mask) & 0xF], False

# COPIED FROM PAFPlayer: art_detail_cell_uses_unicode_glyph; original lines 30448-30460.
def art_detail_cell_uses_unicode_glyph(mode: int, glyph: str) -> bool:
    """Unicode+DRCS rows can mix native Unicode cells and printable DRCS bytes."""
    if ARTWORK_SEAM_STRATEGY in {1, 4} and glyph:
        # While Chafa prepares, the fallback may still contain DRCS bytes.
        return not (len(glyph) == 1 and 0x21 <= ord(glyph) <= 0x7E)
    if not art_detail_uses_unicode_glyphs(mode) or not glyph:
        return False
    # DRCS occupies printable 94-set bytes ! through ~. Space is not a DRCS
    # character and is harmless in either charset, so it need not trigger a
    # charset transition.
    if len(glyph) == 1 and 0x21 <= ord(glyph) <= 0x7E:
        return False
    return glyph != " "

# COPIED FROM PAFPlayer: art_sextant_char; original lines 30463-30465.
def art_sextant_char(mask: int) -> str:
    """Map a row-major 2×3 binary mask to one Unicode sextant glyph."""
    return _SEXTANT_CHAR_BY_MASK.get(int(mask) & 0x3F, " ")

# COPIED FROM PAFPlayer: _OCTANT_SUPPLEMENT_OMITTED_MASKS; original lines 30473-30476.
_OCTANT_SUPPLEMENT_OMITTED_MASKS = frozenset({
    1, 2, 3, 5, 10, 15, 20, 40, 63, 64, 80, 85, 90, 95,
    128, 160, 165, 170, 175, 192, 240, 245, 250, 252,
})

# COPIED FROM PAFPlayer: _OCTANT_SUPPLEMENT_MASK_ORDER; original lines 30477-30479.
_OCTANT_SUPPLEMENT_MASK_ORDER = tuple(
    mask for mask in range(1, 255) if mask not in _OCTANT_SUPPLEMENT_OMITTED_MASKS
)

# COPIED FROM PAFPlayer: _OCTANT_SUPPLEMENT_CHAR_BY_MASK; original lines 30480-30483.
_OCTANT_SUPPLEMENT_CHAR_BY_MASK = {
    mask: chr(0x1CD00 + index)
    for index, mask in enumerate(_OCTANT_SUPPLEMENT_MASK_ORDER)
}

# COPIED FROM PAFPlayer: _OCTANT_EXISTING_GLYPH_BY_MASK: dict[int, tuple[str, bool]]; original lines 30488-30509.
_OCTANT_EXISTING_GLYPH_BY_MASK: dict[int, tuple[str, bool]] = {
    0: (" ", False),
    255: ("█", False),
    3: ("🮂", False),   # upper one quarter block
    252: ("🮂", True),
    5: ("▘", False),             # quadrant upper left
    250: ("▘", True),
    10: ("▝", False),            # quadrant upper right
    245: ("▝", True),
    15: ("▀", False),             # upper half
    240: ("▀", True),
    63: ("🮅", False),  # upper three quarters block
    192: ("🮅", True),
    80: ("▖", False),            # quadrant lower left
    175: ("▖", True),
    85: ("▌", False),            # left half
    170: ("▌", True),
    90: ("▐", False),            # right half
    165: ("▐", True),
    160: ("▗", False),           # quadrant lower right
    95: ("▗", True),
}

# COPIED FROM PAFPlayer: art_octant_char; original lines 30512-30541.
def art_octant_char(mask: int) -> tuple[str, bool]:
    """Return (solid 2×4 mosaic glyph, invert-colors) for a row-major mask."""
    row_major = int(mask) & 0xFF
    existing = _OCTANT_EXISTING_GLYPH_BY_MASK.get(row_major)
    if existing is not None:
        return existing
    direct = _OCTANT_SUPPLEMENT_CHAR_BY_MASK.get(row_major)
    if direct is not None:
        return direct, False
    # Six historical omissions have complements in the Unicode-16 supplement.
    complement = row_major ^ 0xFF
    inverse = _OCTANT_SUPPLEMENT_CHAR_BY_MASK.get(complement)
    if inverse is not None:
        return inverse, True
    # Defensive fallback should be unreachable; degrade to the already-good
    # sextant geometry rather than ever resurrecting Braille.
    collapsed = 0
    # Merge the middle two 2×4 rows into one 2×3 row by majority/OR presence.
    collapsed |= row_major & 0b00000011
    middle_left = bool(row_major & (1 << 2)) or bool(row_major & (1 << 4))
    middle_right = bool(row_major & (1 << 3)) or bool(row_major & (1 << 5))
    if middle_left:
        collapsed |= 1 << 2
    if middle_right:
        collapsed |= 1 << 3
    if row_major & (1 << 6):
        collapsed |= 1 << 4
    if row_major & (1 << 7):
        collapsed |= 1 << 5
    return art_sextant_char(collapsed), False

# COPIED FROM PAFPlayer: _native_art_detail_char; original lines 30545-30554.
def _native_art_detail_char(base_mode: int, mask: int) -> tuple[str, bool]:
    """Return an exact native Unicode glyph for the three hybrid geometries."""
    base = art_detail_base_mode(base_mode)
    if base == 1:
        return art_quadrant_unicode_char(mask)
    if base == 2:
        return art_sextant_char(mask), False
    if base == 3:
        return art_octant_char(mask)
    raise ValueError(f"No native exact artwork mosaic for mode {base_mode}")

# COPIED FROM PAFPlayer: _dense_art_drcs_exact_char; original lines 30557-30570.
def _dense_art_drcs_exact_char(mask: int, source_mode: int, layout_mode: int) -> tuple[str, bool] | None:
    """Return a DRCS glyph only when it represents the source mask exactly."""
    source = art_detail_base_mode(source_mode)
    layout = _normalize_art_detail_layout_mode(layout_mode)
    if source == 1 and layout == 0:
        value = int(mask) & 0xF
        canonical, invert = _canonical_art_detail_mask(value, 4)
        return art_microtile_drcs_char(canonical), invert
    if layout != source or layout < 2:
        return None
    bits = art_detail_subcell_count(source)
    canonical, invert = _canonical_art_detail_mask(int(mask), bits)
    glyph = _art_detail_drcs_char_by_mask(layout).get(canonical)
    return (glyph, invert) if glyph is not None else None

# COPIED FROM PAFPlayer: _hybrid_prefers_native; original lines 30573-30582.
def _hybrid_prefers_native(base_mode: int, mask: int) -> bool:
    """Use native glyphs for simple/common shapes so the EXP mode truly mixes both pools."""
    base = art_detail_base_mode(base_mode)
    columns, rows = art_detail_geometry(base)
    bits = columns * rows
    value = int(mask) & ((1 << bits) - 1)
    # Blank/full and low-complexity contiguous blocks are the safest native
    # terminal glyphs and make a useful test population. More irregular masks
    # prefer exact DRCS when the currently loaded bank contains them.
    return value in {0, (1 << bits) - 1} or _art_detail_mask_edge_complexity(value, columns, rows) <= 2

# COPIED FROM PAFPlayer: _art_detail_quantize_hybrid_cached; original lines 30689-30744.
def _art_detail_quantize_hybrid_cached(
    selector_mode: int, layout_mode: int, flattened_samples: tuple[int, ...],
) -> tuple[tuple[int, int, int], tuple[int, int, int], str]:
    """Exact Unicode+DRCS artwork cell for hybrid 2×2/2×3/2×4 modes."""
    base = art_detail_base_mode(selector_mode)
    samples = tuple(
        tuple(int(flattened_samples[index + channel]) for channel in range(3))
        for index in range(0, len(flattened_samples), 3)
    )
    expected = art_detail_subcell_count(base)
    if len(samples) != expected:
        color = samples[0] if samples else (0, 0, 0)
        return color, color, " "

    best_pair = (0, 1)
    best_distance = -1
    for a in range(len(samples)):
        for b in range(a + 1, len(samples)):
            distance = sum((samples[a][channel] - samples[b][channel]) ** 2 for channel in range(3))
            if distance > best_distance:
                best_distance = distance
                best_pair = (a, b)
    if best_distance <= 0:
        color = samples[0]
        return color, color, " "

    seed_fg, seed_bg = samples[best_pair[0]], samples[best_pair[1]]
    assigned_fg: list[bool] = []
    for sample in samples:
        fg_distance = sum((sample[channel] - seed_fg[channel]) ** 2 for channel in range(3))
        bg_distance = sum((sample[channel] - seed_bg[channel]) ** 2 for channel in range(3))
        assigned_fg.append(fg_distance <= bg_distance)

    def center(want_fg: bool, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
        chosen = [sample for sample, is_fg in zip(samples, assigned_fg) if is_fg == want_fg]
        if not chosen:
            return fallback
        return tuple(round(sum(sample[channel] for sample in chosen) / len(chosen)) for channel in range(3))

    fg, bg = center(True, seed_fg), center(False, seed_bg)
    mask = sum(1 << index for index, is_fg in enumerate(assigned_fg) if is_fg)
    fg_luma = fg[0] * 299 + fg[1] * 587 + fg[2] * 114
    bg_luma = bg[0] * 299 + bg[1] * 587 + bg[2] * 114
    full_mask = (1 << expected) - 1
    if fg_luma < bg_luma:
        fg, bg = bg, fg
        mask ^= full_mask

    exact_drcs = _dense_art_drcs_exact_char(mask, base, layout_mode)
    if exact_drcs is not None and not _hybrid_prefers_native(base, mask):
        glyph, invert = exact_drcs
    else:
        glyph, invert = _native_art_detail_char(base, mask)
    if invert:
        fg, bg = bg, fg
    return fg, bg, glyph

# COPIED FROM PAFPlayer: _art_detail_quantize_seamless_cached; original lines 30748-30798.
def _art_detail_quantize_seamless_cached(
    selector_mode: int, layout_mode: int, codebook_generation: int, flattened_samples: tuple[int, ...],
) -> tuple[tuple[int, int, int], tuple[int, int, int], str]:
    """Exact 2×4 hybrid that uses artwork-adaptive DRCS before Unicode fallback."""
    del codebook_generation  # part of the cache key; active mapping is global
    base = art_detail_base_mode(selector_mode)
    samples = tuple(
        tuple(int(flattened_samples[index + channel]) for channel in range(3))
        for index in range(0, len(flattened_samples), 3)
    )
    expected = art_detail_subcell_count(base)
    if len(samples) != expected:
        color = samples[0] if samples else (0, 0, 0)
        return color, color, " "
    best_pair = (0, 1)
    best_distance = -1
    for a in range(len(samples)):
        for b in range(a + 1, len(samples)):
            distance = sum((samples[a][channel] - samples[b][channel]) ** 2 for channel in range(3))
            if distance > best_distance:
                best_distance = distance
                best_pair = (a, b)
    if best_distance <= 0:
        color = samples[0]
        return color, color, " "
    seed_fg, seed_bg = samples[best_pair[0]], samples[best_pair[1]]
    assigned_fg: list[bool] = []
    for sample in samples:
        fg_distance = sum((sample[channel] - seed_fg[channel]) ** 2 for channel in range(3))
        bg_distance = sum((sample[channel] - seed_bg[channel]) ** 2 for channel in range(3))
        assigned_fg.append(fg_distance <= bg_distance)
    def center(want_fg: bool, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
        chosen = [sample for sample, is_fg in zip(samples, assigned_fg) if is_fg == want_fg]
        if not chosen:
            return fallback
        return tuple(round(sum(sample[channel] for sample in chosen) / len(chosen)) for channel in range(3))
    fg, bg = center(True, seed_fg), center(False, seed_bg)
    mask = sum(1 << index for index, is_fg in enumerate(assigned_fg) if is_fg)
    fg_luma = fg[0] * 299 + fg[1] * 587 + fg[2] * 114
    bg_luma = bg[0] * 299 + bg[1] * 587 + bg[2] * 114
    if fg_luma < bg_luma:
        fg, bg = bg, fg
        mask ^= (1 << expected) - 1
    exact_drcs = _dense_art_drcs_exact_char(mask, base, layout_mode)
    if exact_drcs is not None:
        glyph, invert = exact_drcs
    else:
        glyph, invert = _native_art_detail_char(base, mask)
    if invert:
        fg, bg = bg, fg
    return fg, bg, glyph

# COPIED FROM PAFPlayer: _resample_art_detail_samples; original lines 30801-30817.
def _resample_art_detail_samples(
    samples: tuple[tuple[int, int, int], ...], source_mode: int, target_mode: int,
) -> tuple[tuple[int, int, int], ...]:
    """Nearest-neighbor resample RGB subcells between artwork-detail geometries."""
    source = art_detail_base_mode(source_mode)
    target = art_detail_base_mode(target_mode)
    source_columns, source_rows = art_detail_geometry(source)
    target_columns, target_rows = art_detail_geometry(target)
    if len(samples) != source_columns * source_rows:
        return tuple()
    result: list[tuple[int, int, int]] = []
    for target_row in range(target_rows):
        source_row = min(source_rows - 1, max(0, int((target_row + 0.5) * source_rows / target_rows)))
        for target_column in range(target_columns):
            source_column = min(source_columns - 1, max(0, int((target_column + 0.5) * source_columns / target_columns)))
            result.append(samples[source_row * source_columns + source_column])
    return tuple(result)

# COPIED FROM PAFPlayer: _art_detail_quantize_adaptive_exact_cached; original lines 30821-30887.
def _art_detail_quantize_adaptive_exact_cached(
    selector_mode: int, layout_mode: int, flattened_samples: tuple[int, ...],
) -> tuple[tuple[int, int, int], tuple[int, int, int], str]:
    """Never approximate a high-density mask: exact DRCS or exact 2×4 fallback.

    The 3×3/2×5/3×4 adaptive modes expose more detail when the requested mask
    happens to be one of the 55 exact shapes in the active DRCS bank. A miss is
    deliberately *not* mapped to the nearest high-density shape; instead the RGB
    samples are resampled to 2×4 and rendered with the universal exact octant
    Unicode+DRCS vocabulary. Thus every displayed glyph is geometrically exact
    for the resolution actually used in that cell.
    """
    base = art_detail_base_mode(selector_mode)
    samples = tuple(
        tuple(int(flattened_samples[index + channel]) for channel in range(3))
        for index in range(0, len(flattened_samples), 3)
    )
    expected = art_detail_subcell_count(base)
    if len(samples) != expected:
        color = samples[0] if samples else (0, 0, 0)
        return color, color, " "

    best_pair = (0, 1)
    best_distance = -1
    for a in range(len(samples)):
        for b in range(a + 1, len(samples)):
            distance = sum((samples[a][channel] - samples[b][channel]) ** 2 for channel in range(3))
            if distance > best_distance:
                best_distance = distance
                best_pair = (a, b)
    if best_distance <= 0:
        color = samples[0]
        return color, color, " "

    seed_fg, seed_bg = samples[best_pair[0]], samples[best_pair[1]]
    assigned_fg: list[bool] = []
    for sample in samples:
        fg_distance = sum((sample[channel] - seed_fg[channel]) ** 2 for channel in range(3))
        bg_distance = sum((sample[channel] - seed_bg[channel]) ** 2 for channel in range(3))
        assigned_fg.append(fg_distance <= bg_distance)

    def center(want_fg: bool, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
        chosen = [sample for sample, is_fg in zip(samples, assigned_fg) if is_fg == want_fg]
        if not chosen:
            return fallback
        return tuple(round(sum(sample[channel] for sample in chosen) / len(chosen)) for channel in range(3))

    fg, bg = center(True, seed_fg), center(False, seed_bg)
    mask = sum(1 << index for index, is_fg in enumerate(assigned_fg) if is_fg)
    fg_luma = fg[0] * 299 + fg[1] * 587 + fg[2] * 114
    bg_luma = bg[0] * 299 + bg[1] * 587 + bg[2] * 114
    if fg_luma < bg_luma:
        fg, bg = bg, fg
        mask ^= (1 << expected) - 1

    exact_drcs = _dense_art_drcs_exact_char(mask, base, layout_mode)
    if exact_drcs is not None:
        glyph, invert = exact_drcs
        if invert:
            fg, bg = bg, fg
        return fg, bg, glyph

    # Exact high-density miss: intentionally reduce spatial resolution rather
    # than inventing an incorrect subcell. Mode 9's 2×4 hybrid is universal.
    fallback_samples = _resample_art_detail_samples(samples, base, 3)
    fallback_flat = tuple(channel for rgb in fallback_samples for channel in rgb)
    return _art_detail_quantize_hybrid_cached(9, layout_mode, fallback_flat)

# COPIED FROM PAFPlayer: _art_detail_quantize_cached; original lines 30891-30960.
def _art_detail_quantize_cached(
    mode: int, flattened_samples: tuple[int, ...],
) -> tuple[tuple[int, int, int], tuple[int, int, int], str]:
    """Cluster 4/6/8 artwork samples to FG/BG plus a matching detail glyph."""
    mode = max(1, min(3, int(mode)))
    samples = tuple(
        tuple(int(flattened_samples[index + channel]) for channel in range(3))
        for index in range(0, len(flattened_samples), 3)
    )
    expected = {1: 4, 2: 6, 3: 8}[mode]
    if len(samples) != expected:
        color = samples[0] if samples else (0, 0, 0)
        return color, color, " "
    best_pair = (0, 1)
    best_distance = -1
    for a in range(len(samples)):
        for b in range(a + 1, len(samples)):
            distance = sum((samples[a][i] - samples[b][i]) ** 2 for i in range(3))
            if distance > best_distance:
                best_distance = distance
                best_pair = (a, b)
    if best_distance <= 0:
        color = samples[0]
        if mode == 1:
            glyph = art_microtile_drcs_char(0)
        elif mode == 2:
            glyph = art_sextant_char(0)
        else:
            glyph, _invert = art_octant_char(0)
        return color, color, glyph
    seed_fg, seed_bg = samples[best_pair[0]], samples[best_pair[1]]
    assigned_fg: list[bool] = []
    for sample in samples:
        fg_distance = sum((sample[i] - seed_fg[i]) ** 2 for i in range(3))
        bg_distance = sum((sample[i] - seed_bg[i]) ** 2 for i in range(3))
        assigned_fg.append(fg_distance <= bg_distance)

    def center(want_fg: bool, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
        chosen = [sample for sample, is_fg in zip(samples, assigned_fg) if is_fg == want_fg]
        if not chosen:
            return fallback
        return tuple(round(sum(sample[i] for sample in chosen) / len(chosen)) for i in range(3))

    fg, bg = center(True, seed_fg), center(False, seed_bg)
    mask = sum(1 << index for index, is_fg in enumerate(assigned_fg) if is_fg)
    if mode == 1:
        canonical = min(mask, mask ^ 0xF)
        if canonical != mask:
            fg, bg = bg, fg
        glyph = art_microtile_drcs_char(canonical)
    else:
        # V373 anti-banding: dense glyph modes previously let whichever extreme
        # sample happened to be encountered first become ANSI foreground. Across
        # smooth art that role could flip from cell to cell/row to row, exposing
        # font-edge/fallback seams as visible bands. Keep the brighter cluster as
        # foreground and complement the shape when necessary; pixels are the same,
        # but FG/BG semantics stay spatially stable and SGR churn drops.
        fg_luma = fg[0] * 299 + fg[1] * 587 + fg[2] * 114
        bg_luma = bg[0] * 299 + bg[1] * 587 + bg[2] * 114
        full_mask = 0x3F if mode == 2 else 0xFF
        if fg_luma < bg_luma:
            fg, bg = bg, fg
            mask ^= full_mask
        if mode == 2:
            glyph = art_sextant_char(mask)
        else:
            glyph, invert = art_octant_char(mask)
            if invert:
                fg, bg = bg, fg
    return fg, bg, glyph

# COPIED FROM PAFPlayer: _art_detail_quantize_drcs_cached; original lines 30992-31050.
def _art_detail_quantize_drcs_cached(
    mode: int, layout_mode: int, flattened_samples: tuple[int, ...],
) -> tuple[tuple[int, int, int], tuple[int, int, int], str]:
    """Cluster artwork samples to two colors and one fixed-cell DRCS mosaic."""
    mode = max(1, min(len(ART_MICROTILE_DETAIL_MODE_GEOMETRIES) - 1, int(mode)))
    layout = _normalize_art_detail_layout_mode(layout_mode)
    samples = tuple(
        tuple(int(flattened_samples[index + channel]) for channel in range(3))
        for index in range(0, len(flattened_samples), 3)
    )
    expected = art_detail_subcell_count(mode)
    if len(samples) != expected:
        color = samples[0] if samples else (0, 0, 0)
        glyph, _invert = dense_art_drcs_char(0, mode, layout)
        return color, color, glyph

    best_pair = (0, 1)
    best_distance = -1
    for a in range(len(samples)):
        for b in range(a + 1, len(samples)):
            distance = sum((samples[a][channel] - samples[b][channel]) ** 2 for channel in range(3))
            if distance > best_distance:
                best_distance = distance
                best_pair = (a, b)
    if best_distance <= 0:
        color = samples[0]
        glyph, _invert = dense_art_drcs_char(0, mode, layout)
        return color, color, glyph

    seed_fg, seed_bg = samples[best_pair[0]], samples[best_pair[1]]
    assigned_fg: list[bool] = []
    for sample in samples:
        fg_distance = sum((sample[channel] - seed_fg[channel]) ** 2 for channel in range(3))
        bg_distance = sum((sample[channel] - seed_bg[channel]) ** 2 for channel in range(3))
        assigned_fg.append(fg_distance <= bg_distance)

    def center(want_fg: bool, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
        chosen = [sample for sample, is_fg in zip(samples, assigned_fg) if is_fg == want_fg]
        if not chosen:
            return fallback
        return tuple(round(sum(sample[channel] for sample in chosen) / len(chosen)) for channel in range(3))

    fg, bg = center(True, seed_fg), center(False, seed_bg)
    mask = sum(1 << index for index, is_fg in enumerate(assigned_fg) if is_fg)

    # Keep the brighter color as foreground. This reduces SGR role-flipping and
    # lets complementary masks share one downloaded glyph without changing the
    # actual two-color pixels.
    fg_luma = fg[0] * 299 + fg[1] * 587 + fg[2] * 114
    bg_luma = bg[0] * 299 + bg[1] * 587 + bg[2] * 114
    full_mask = (1 << art_detail_subcell_count(mode)) - 1
    if fg_luma < bg_luma:
        fg, bg = bg, fg
        mask ^= full_mask

    glyph, invert = dense_art_drcs_char(mask, mode, layout)
    if invert:
        fg, bg = bg, fg
    return fg, bg, glyph

# COPIED FROM PAFPlayer: define_all_player_drcs; original lines 31053-31080.
def define_all_player_drcs(dense_art_layout: int | bool = False) -> str:
    """Download the mode-specific fixed-cell soft font used by the visualizer.

    Legacy/2×2 keeps the historical 9×9 twin bars and eight exact quadrant
    masks. 2×3 uses a 7×7 bar bank plus all 32 exact sextant masks. 2×4, 3×3,
    2×5 and 3×4 use 6×6 bars plus 55 geometry-specific artwork masks. The
    remaining slots, if any, are blank fillers so | } ~ stay the volume glyphs.
    """
    layout_mode = _normalize_art_detail_layout_mode(dense_art_layout)
    volume_payload = define_volume_drcs().split("{ @", 1)[1][:-2]
    blank = _drcs_pattern(tuple(".........." for _row in range(20)))
    if layout_mode:
        twin_levels = ART_DETAIL_DRCS_TWIN_LEVELS_BY_MODE[layout_mode]
        twin_patterns = define_twin_visualizer_drcs_patterns(twin_levels)
        art_patterns = define_dense_art_drcs_patterns(layout_mode)
        filler_count = 94 - 3 - len(twin_patterns) - len(art_patterns)
        if filler_count < 0:
            raise AssertionError("DRCS bank overflow")
        payload = ";".join((*twin_patterns, *art_patterns, *([blank] * filler_count), volume_payload))
        assert len(twin_patterns) + len(art_patterns) + filler_count + 3 == 94
    else:
        twin_patterns = define_twin_visualizer_drcs_patterns()
        microtiles = define_art_microtile_drcs_patterns()
        # !..q = 81 twin bars; r..y = eight exact 2×2 masks; z/{ blank;
        # |/}/~ retain the three speaker pieces.
        filler_count = 92 - (1 + len(twin_patterns) + len(microtiles))
        payload = ";".join((*twin_patterns, *microtiles, *([blank] * filler_count), volume_payload))
    return "\033P0;1;1;10;0;2;20;0{ @" + payload + "\033\\"

# COPIED FROM PAFPlayer: _visualizer_ansi_fg_bg_cached; original lines 32526-32536.
def _visualizer_ansi_fg_bg_cached(
    red: int, green: int, blue: int,
    background_red: int, background_green: int, background_blue: int,
) -> str:
    """Emit foreground + optional background in one SGR for tall Twin DRCS frames."""
    if background_red < 0:
        return f"\033[38;2;{red};{green};{blue};49m"
    return (
        f"\033[38;2;{red};{green};{blue};"
        f"48;2;{background_red};{background_green};{background_blue}m"
    )

# COPIED FROM PAFPlayer: _VISUALIZER_ART_SCALE_CACHE: dict[tuple[int, int, int], tuple[object, tuple[tuple[tuple[int, int, int], ...], ...]]]; original lines 32544-32544.
_VISUALIZER_ART_SCALE_CACHE: dict[tuple[int, int, int], tuple[object, tuple[tuple[tuple[int, int, int], ...], ...]]] = {}

# COPIED FROM PAFPlayer: _visualizer_scaled_art_grid; original lines 32556-32597.
def _visualizer_scaled_art_grid(
    grid: tuple[tuple[tuple[int, int, int], ...], ...] | None,
    strength: float,
    quantize_step: int = 1,
) -> tuple[tuple[tuple[int, int, int], ...], ...]:
    if not grid:
        return tuple()
    strength_step = max(0, min(1000, round(float(strength) * 1000.0)))
    if strength_step <= 0:
        return tuple()
    quantize = max(1, int(quantize_step))
    key = (id(grid), strength_step, quantize)
    cached = _VISUALIZER_ART_SCALE_CACHE.get(key)
    if cached is not None and cached[0] is grid:
        return cached[1]
    factor = strength_step / 1000.0
    if quantize == 1:
        scaled = tuple(
            tuple(
                tuple(max(0, min(255, round(channel * factor))) for channel in rgb)
                for rgb in row
            )
            for row in grid
        )
    else:
        scaled = tuple(
            tuple(
                tuple(
                    min(255, round((channel * factor) / quantize) * quantize)
                    for channel in rgb
                )
                for rgb in row
            )
            for row in grid
        )
    # Keep this deliberately tiny: normally there are only two entries for the
    # current art (bar-weighted and blackness-weighted).  Holding the source
    # object alongside the result also prevents an id-reuse false cache hit.
    if len(_VISUALIZER_ART_SCALE_CACHE) >= 8:
        _VISUALIZER_ART_SCALE_CACHE.pop(next(iter(_VISUALIZER_ART_SCALE_CACHE)))
    _VISUALIZER_ART_SCALE_CACHE[key] = (grid, scaled)
    return scaled

# COPIED FROM PAFPlayer: _art_microtile_quantize_cached; original lines 32601-32634.
def _art_microtile_quantize_cached(
    tlr: int, tlg: int, tlb: int, trr: int, trg: int, trb: int,
    blr: int, blg: int, blb: int, brr: int, brg: int, brb: int,
) -> tuple[tuple[int, int, int], tuple[int, int, int], str]:
    """Approximate four artwork samples with two colors and one 2×2 DRCS mask."""
    samples = ((tlr, tlg, tlb), (trr, trg, trb), (blr, blg, blb), (brr, brg, brb))
    best_pair = (0, 1)
    best_distance = -1
    for a in range(4):
        for b in range(a + 1, 4):
            distance = sum((samples[a][i] - samples[b][i]) ** 2 for i in range(3))
            if distance > best_distance:
                best_distance = distance
                best_pair = (a, b)
    if best_distance <= 0:
        color = samples[0]
        return color, color, art_microtile_drcs_char(0)
    seed_fg, seed_bg = samples[best_pair[0]], samples[best_pair[1]]
    assigned_fg: list[bool] = []
    for sample in samples:
        fg_distance = sum((sample[i] - seed_fg[i]) ** 2 for i in range(3))
        bg_distance = sum((sample[i] - seed_bg[i]) ** 2 for i in range(3))
        assigned_fg.append(fg_distance <= bg_distance)
    def center(want_fg: bool, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
        chosen = [sample for sample, is_fg in zip(samples, assigned_fg) if is_fg == want_fg]
        if not chosen:
            return fallback
        return tuple(round(sum(sample[i] for sample in chosen) / len(chosen)) for i in range(3))
    fg, bg = center(True, seed_fg), center(False, seed_bg)
    mask = sum(1 << index for index, is_fg in enumerate(assigned_fg) if is_fg)
    canonical = min(mask, mask ^ 0xF)
    if canonical != mask:
        fg, bg = bg, fg
    return fg, bg, art_microtile_drcs_char(canonical)

# COPIED FROM PAFPlayer: fill_artwork_vertical_gaps; original lines 32825-32842.
def fill_artwork_vertical_gaps(rows):
    """Experimental: fill only isolated dark cells between bright neighbors.

    Glyph overhang itself is font-dependent; this addresses quantized one-cell
    dark dividers, and can also remove real dark detail. Never enabled by default.
    """
    result = []
    for row in rows:
        cells = list(row)
        for column in range(1, len(row) - 1):
            left, here, right = row[column - 1:column + 2]
            luminance = lambda cell: max(sum(cell[0]), sum(cell[1])) / 3
            if luminance(here) <= 8 and min(luminance(left), luminance(right)) >= 40:
                color = tuple(round((left[0][c] + right[0][c]) / 2) for c in range(3))
                # A space painted with a solid background uses no font bounds.
                cells[column] = (color, color, " ")
        result.append(tuple(cells))
    return tuple(result)

# COPIED FROM PAFPlayer: _CHAFA_SYMBOL_CACHE; original lines 32845-32845.
_CHAFA_SYMBOL_CACHE = {}

# COPIED FROM PAFPlayer: _CHAFA_SYMBOL_PENDING; original lines 32846-32846.
_CHAFA_SYMBOL_PENDING = set()

# COPIED FROM PAFPlayer: _CHAFA_SYMBOL_LOCK; original lines 32847-32847.
_CHAFA_SYMBOL_LOCK = threading.Lock()

# COPIED FROM PAFPlayer: chafa_symbol_art_cells; original lines 32850-32873.
def chafa_symbol_art_cells(grid, columns, rows):
    key = (id(grid), columns, rows, terminal_cell_pixel_size_nonintrusive())
    with _CHAFA_SYMBOL_LOCK:
        cached = _CHAFA_SYMBOL_CACHE.get(key)
        if cached is not None and cached[0] is grid:
            return cached[1]
        if key in _CHAFA_SYMBOL_PENDING:
            return ()
        _CHAFA_SYMBOL_PENDING.add(key)
    def prepare():
        try:
            result = _render_chafa_symbol_art_cells(grid, columns, rows)
            with _CHAFA_SYMBOL_LOCK:
                if len(_CHAFA_SYMBOL_CACHE) >= 4:
                    _CHAFA_SYMBOL_CACHE.pop(next(iter(_CHAFA_SYMBOL_CACHE)))
                _CHAFA_SYMBOL_CACHE[key] = (grid, result)
            # Discard the temporary ordinary-glyph fallback when Chafa is ready.
            _VISUALIZER_ART_DETAIL_GRID_CACHE.clear()
            _VISUALIZER_ART_CELL_STYLE_CACHE.clear()
        finally:
            with _CHAFA_SYMBOL_LOCK:
                _CHAFA_SYMBOL_PENDING.discard(key)
    threading.Thread(target=prepare, name="paf-chafa-symbols", daemon=True).start()
    return ()

# COPIED FROM PAFPlayer: _render_chafa_symbol_art_cells; original lines 32876-32926.
def _render_chafa_symbol_art_cells(grid, columns, rows):
    """Render a cached artwork grid with measured cell aspect and parse its cells."""
    chafa = shutil.which("chafa")
    if not chafa or not grid:
        return ()
    try:
        from PIL import Image
        cw, ch = terminal_cell_pixel_size_nonintrusive()
        image = Image.new("RGB", (len(grid[0]), len(grid)))
        image.putdata([rgb for row in grid for rgb in row])
        image = image.resize((columns * cw, rows * ch))
        stream = io.BytesIO(); image.save(stream, format="PNG")
        process = subprocess.run([chafa, "--format=symbols", "--colors=full",
            "--symbols=half+solid+space", "--optimize=0", "--relative=off", "--probe=off",
            "--animate=off", "--threads=1", "--work=3", "--scale=max",
            f"--font-ratio={cw}/{ch}", f"--size={columns}x{rows}", "-"],
            input=stream.getvalue(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=3.0, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if process.returncode:
            return ()
        output = []; fg = (255, 255, 255); bg = (0, 0, 0)
        for line in process.stdout.decode("utf-8", errors="replace").splitlines()[:rows]:
            cells = []; index = 0
            while index < len(line):
                ansi = ANSI_CSI_RE.match(line, index)
                if ansi:
                    token = ansi.group(0)
                    if token.endswith("m"):
                        codes = [int(n or 0) for n in token[2:-1].split(";")]
                        j = 0
                        while j < len(codes):
                            code = codes[j]
                            if code in (38, 48) and j + 4 < len(codes) and codes[j + 1] == 2:
                                rgb = tuple(codes[j + 2:j + 5])
                                if code == 38: fg = rgb
                                else: bg = rgb
                                j += 5; continue
                            if code in (0, 39): fg = (255, 255, 255)
                            if code in (0, 49): bg = (0, 0, 0)
                            j += 1
                    index = ansi.end(); continue
                glyph = line[index]; index += 1
                if glyph in " ▀▄▌▐█" and len(cells) < columns:
                    cells.append((fg, bg, glyph))
            cells.extend([((0, 0, 0), (0, 0, 0), " ")] * (columns - len(cells)))
            output.append(tuple(cells))
        if len(output) != rows:
            return ()
        return tuple(output)
    except (ImportError, OSError, ValueError, subprocess.TimeoutExpired):
        return ()

# COPIED FROM PAFPlayer: _VISUALIZER_ART_DETAIL_GRID_CACHE: dict[tuple[int, int, int, int, int, int], tuple[object, tuple[tuple[tuple[tuple[int, int, int], tuple[int, int, int], str], ...], ...]]]; original lines 32929-32932.
_VISUALIZER_ART_DETAIL_GRID_CACHE: dict[
    tuple[int, int, int, int, int, int],
    tuple[object, tuple[tuple[tuple[tuple[int, int, int], tuple[int, int, int], str], ...], ...]],
] = {}

# COPIED FROM PAFPlayer: _visualizer_art_microtiles; original lines 32935-33025.
def _visualizer_art_microtiles(
    grid: tuple[tuple[tuple[int, int, int], ...], ...] | None,
    source_rows: int, terminal_width: int, strength: float,
    detail_mode: int = ART_MICROTILE_DETAIL_MODE_DEFAULT,
    dense_drcs_layout: int | bool = False,
) -> tuple[tuple[tuple[tuple[int, int, int], tuple[int, int, int], str], ...], ...]:
    """Convert cached artwork samples into two-color within-cell DRCS mosaics.

    The source grid is generated at the maximum horizontal/vertical subcell
    resolution required by the two artwork layers. Each layer then samples the
    centers of its own geometry (2×2, 2×3, 2×4, 3×3, 2×5 or 3×4). This lets a
    3-wide mode coexist with a 2-wide mode without rebuilding the album strip.
    """
    mode = max(0, min(len(ART_MICROTILE_DETAIL_MODE_NAMES) - 1, int(detail_mode)))
    if mode <= 0 or not grid or source_rows <= 0 or terminal_width <= 0:
        return tuple()
    layout_mode = _normalize_art_detail_layout_mode(dense_drcs_layout)
    strength_step = max(0, min(1000, round(float(strength) * 1000.0)))
    cache_key = (id(grid), int(source_rows), int(terminal_width), strength_step, mode, layout_mode, ARTWORK_SEAM_STRATEGY)
    cached = _VISUALIZER_ART_DETAIL_GRID_CACHE.get(cache_key)
    if cached is not None and cached[0] is grid:
        return cached[1]

    scaled = _visualizer_scaled_art_grid(grid, strength, 1)
    if not scaled:
        return tuple()
    source_vertical = len(scaled) // source_rows
    if source_vertical <= 0:
        return tuple()
    minimum_row_width = min((len(row) for row in scaled[: source_rows * source_vertical]), default=0)
    source_horizontal = minimum_row_width // terminal_width
    wanted_horizontal = art_detail_horizontal_subcells(mode)
    wanted_vertical = art_detail_vertical_subcells(mode)
    if source_horizontal < wanted_horizontal or source_vertical < wanted_vertical:
        return tuple()

    sampled_row_offsets = []
    for subrow in range(wanted_vertical):
        relative = round(((subrow + 0.5) * source_vertical / wanted_vertical) - 0.5)
        sampled_row_offsets.append(max(0, min(source_vertical - 1, relative)))
    sampled_column_offsets = []
    for subcolumn in range(wanted_horizontal):
        relative = round(((subcolumn + 0.5) * source_horizontal / wanted_horizontal) - 0.5)
        sampled_column_offsets.append(max(0, min(source_horizontal - 1, relative)))

    chafa_cells = chafa_symbol_art_cells(grid, terminal_width, source_rows) if ARTWORK_SEAM_STRATEGY == 4 else ()
    output = []
    for row in range(source_rows):
        cells = []
        for column in range(terminal_width):
            base_column = column * source_horizontal
            samples: list[tuple[int, int, int]] = []
            for row_offset in sampled_row_offsets:
                source_row = scaled[row * source_vertical + row_offset]
                for column_offset in sampled_column_offsets:
                    samples.append(source_row[base_column + column_offset])
            flattened = tuple(channel for rgb in samples for channel in rgb)
            if chafa_cells:
                fg, bg, glyph = chafa_cells[row][column]
                cells.append((tuple(round(c * strength_step / 1000) for c in fg),
                              tuple(round(c * strength_step / 1000) for c in bg), glyph))
            elif ARTWORK_SEAM_STRATEGY == 1:
                color = tuple(round(sum(rgb[c] for rgb in samples) / len(samples)) for c in range(3))
                glyph = "██\033[1D" if column + 1 < terminal_width else "█"
                cells.append((color, color, glyph))
            elif ARTWORK_SEAM_STRATEGY == 5:
                # Native half blocks only if no DRCS bank is loaded; otherwise
                # quantize every artwork cell into the same downloaded bank.
                if layout_mode:
                    cells.append(_art_detail_quantize_drcs_cached(mode, layout_mode, flattened))
                else:
                    cells.append(_art_detail_quantize_cached(min(3, art_detail_base_mode(mode)), flattened))
            elif art_detail_is_seamless_adaptive(mode):
                cells.append(_art_detail_quantize_seamless_cached(mode, layout_mode, _ART_DETAIL_DRCS_OVERRIDE_GENERATION, flattened))
            elif art_detail_is_adaptive_exact(mode):
                cells.append(_art_detail_quantize_adaptive_exact_cached(mode, layout_mode, flattened))
            elif art_detail_is_hybrid(mode):
                cells.append(_art_detail_quantize_hybrid_cached(mode, layout_mode, flattened))
            elif layout_mode:
                cells.append(_art_detail_quantize_drcs_cached(mode, layout_mode, flattened))
            elif mode == 1 and len(samples) == 4:
                cells.append(_art_microtile_quantize_cached(*flattened))
            else:
                # Defensive fallback for an unexpected bank transition.
                cells.append(_art_detail_quantize_cached(min(3, art_detail_base_mode(mode)), flattened))
        output.append(tuple(cells))
    result = fill_artwork_vertical_gaps(tuple(output)) if ARTWORK_SEAM_STRATEGY == 2 else tuple(output)
    if len(_VISUALIZER_ART_DETAIL_GRID_CACHE) >= 12:
        _VISUALIZER_ART_DETAIL_GRID_CACHE.pop(next(iter(_VISUALIZER_ART_DETAIL_GRID_CACHE)))
    _VISUALIZER_ART_DETAIL_GRID_CACHE[cache_key] = (grid, result)
    return result

# COPIED FROM PAFPlayer: _VISUALIZER_ART_CELL_STYLE_CACHE: dict; original lines 33028-33028.
_VISUALIZER_ART_CELL_STYLE_CACHE: dict = {}

# COPIED FROM PAFPlayer: _visualizer_art_cell_styles; original lines 33031-33056.
def _visualizer_art_cell_styles(grid, detail_mode: int, terminal_width: int):
    """Cache immutable background cells' SGR, charset and cursor fences.

    Keep a source reference alongside each identity key to prevent id reuse.
    New artwork, strength, dimensions or a DRCS bank swap yields a new grid;
    the Unicode mode and fence setting are also part of this bounded cache.
    """
    key = (id(grid), detail_mode, terminal_width, bool(HYBRID_UNICODE_CURSOR_FENCE))
    cached = _VISUALIZER_ART_CELL_STYLE_CACHE.get(key)
    if cached is not None and cached[0] is grid:
        return cached[1]
    result = []
    for row in grid:
        cells = []
        for column, (color, background, glyph) in enumerate(row):
            unicode_art = art_detail_cell_uses_unicode_glyph(detail_mode, glyph)
            sgr = _visualizer_ansi_fg_bg_cached(*color, *background)
            if HYBRID_UNICODE_CURSOR_FENCE and unicode_art and column + 1 < terminal_width:
                glyph += f"\033[{column + 2}G"
            cells.append((color, background, sgr, glyph, unicode_art))
        result.append(tuple(cells))
    result = tuple(result)
    if len(_VISUALIZER_ART_CELL_STYLE_CACHE) >= 4:
        _VISUALIZER_ART_CELL_STYLE_CACHE.pop(next(iter(_VISUALIZER_ART_CELL_STYLE_CACHE)))
    _VISUALIZER_ART_CELL_STYLE_CACHE[key] = (grid, result)
    return result

