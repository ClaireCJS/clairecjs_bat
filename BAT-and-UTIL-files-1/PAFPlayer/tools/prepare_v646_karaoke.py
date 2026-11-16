"""Apply the measured karaoke hot-path fix with verified replacement backups."""
import ast
import hashlib
from prepare_v642_artwork_chrome import ROOT, write


def main():
    path = ROOT/'PAFPlayer.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == '10023982c74ef26fc41305dac1ffc8ff3653eec803a31462562a10aea6ed0535'
    source = path.read_text(encoding='utf-8')

    def change(before, after):
        nonlocal source
        assert source.count(before) == 1, before[:100]
        source = source.replace(before, after, 1)

    change("PROGRAM_VERSION                = 'V645'", "PROGRAM_VERSION                = 'V646'")
    change("PROGRAM_RELEASE_LABEL          = 'V645'", "PROGRAM_RELEASE_LABEL          = 'V646'")
    change("'2026-11-06-v645-artwork-window-controls'", "'2026-11-09-v646-karaoke-render-load'")
    tree = ast.parse(source)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'emojimax_solution_label_color')
    old = ast.get_source_segment(source, fn)
    begin = old[:old.index('    middle =')]
    change(old, begin + '''    # Do area-sized work in Pillow, not millions of Python getpixel calls.
    # Colored emoji can leave this entire monochrome mask region empty.
    from PIL import Image, ImageChops
    region = (x0, y0, x1, y1)
    coverage = source_mask.crop(region) if source_mask is not None else None
    if coverage is not None and coverage.getbbox() is None:
        return fallback
    channels = len(source_rgba.getbands())
    if channels < 3:
        return fallback
    if channels >= 4:
        alpha = source_rgba.crop(region).getchannel(3)
        coverage = ImageChops.darker(coverage, alpha) if coverage is not None else alpha
    elif coverage is None:
        coverage = Image.new("L", (x1 - x0, y1 - y0), 255)
    # Keep the original selection order: solid before antialiased, leftmost
    # column first, then the row nearest the center (upper row wins ties).
    height = y1 - y0
    split = (height + 1) // 2
    middle = (height - 1) / 2.0
    for threshold in (200, 96):
        eligible = coverage.point([0] * threshold + [255] * (256 - threshold))
        bounds = eligible.getbbox()
        if bounds is None:
            continue
        x = bounds[0]
        column = eligible.crop((x, 0, x + 1, height)).tobytes()
        above = column.rfind(b"\\xff", 0, split)
        below = column.find(b"\\xff", split)
        y = min((row for row in (above, below) if row >= 0),
                key=lambda row: (abs(row - middle), row))
        pixel = source_rgba.getpixel((x0 + x, y0 + y))
        return f"#{int(pixel[0]):02x}{int(pixel[1]):02x}{int(pixel[2]):02x}"
    return fallback''')
    change('''            """Build a fitted over-art lyric layer; use vectors for huge simple cues."""
            state["artwork_lyric_rgba"] = None''', '''            """Build a fitted over-art lyric layer; use vectors for huge simple cues."""
            # This repaint already draws the current phase. Cancel the previous
            # cue's animation so it cannot immediately redraw the fresh layer.
            pending = state.get("artwork_lyric_color_after")
            if pending is not None:
                with contextlib.suppress(Exception):
                    root.after_cancel(pending)
            state["artwork_lyric_color_after"] = None
            state["artwork_lyric_rgba"] = None''')
    change('''                pixel_area = int(mask.size[0]) * int(mask.size[1]) if mask is not None else 0
                animation_ms = 90 if pixel_area < 180_000 else (140 if pixel_area < 500_000 else 220)''', '''                animation_ms = artwork_lyric_animation_interval_ms()''')
    change('''        def ensure_artwork_lyric_color_animation() -> None:''', '''        def artwork_lyric_animation_interval_ms() -> int:
            """Use the existing cadence for both first and subsequent recolors."""
            if state.get("artwork_lyric_native_items") and state.get("artwork_lyric_native_mode"):
                return ARTWORK_LYRIC_NATIVE_FAST_PATH_TICK_MS
            mask = state.get("artwork_lyric_plasma_mask")
            if mask is not None:
                pixel_area = int(mask.size[0]) * int(mask.size[1])
                return 90 if pixel_area < 180_000 else (140 if pixel_area < 500_000 else 220)
            return 150

        def ensure_artwork_lyric_color_animation() -> None:''')
    change('''                state["artwork_lyric_color_after"] = root.after(0, animate_artwork_lyric_colors)''', '''                state["artwork_lyric_color_after"] = root.after(
                    artwork_lyric_animation_interval_ms(), animate_artwork_lyric_colors)''')
    compile(source, str(path), 'exec')
    write('PAFPlayer.py', source)


if __name__ == '__main__':
    main()
