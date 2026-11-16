"""Remove the artwork lyric size ceiling; preserve verified replacement backups."""
import hashlib
from prepare_v642_artwork_chrome import ROOT, write


def main():
    path = ROOT / 'PAFPlayer.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == '227f607b020d7f153761ccac00c6dec97c92687979a67896126df828ada65f48'
    source = path.read_text(encoding='utf-8')

    def change(old, new):
        nonlocal source
        assert source.count(old) == 1, (old[:80], source.count(old))
        source = source.replace(old, new, 1)

    change("'2026-11-04-v642-artwork-popup-chrome'", "'2026-11-05-v643-artwork-karaoke-fit'")
    change("PROGRAM_VERSION                = 'V642'", "PROGRAM_VERSION                = 'V643'")
    change("PROGRAM_RELEASE_LABEL          = 'V642'", "PROGRAM_RELEASE_LABEL          = 'V643'")
    change('''        def adjust_artwork_lyric_zoom(direction: int) -> str:
            current = float(state.get("lyric_font_scale", 1.0) or 1.0)''', '''        def adjust_artwork_lyric_zoom(direction: int) -> str:
            # V643: 100% is the largest fitting size. Accept old saved values
            # above 100%, but let the first zoom-out immediately reduce the cue.
            current = min(1.0, float(state.get("lyric_font_scale", 1.0) or 1.0))''')
    change('''                min(EXTERNAL_ALBUM_ART_LYRIC_FONT_SCALE_MAX, next_scale),''', '''                min(1.0, next_scale),''')
    change('''            desired_size = max(12, min(260, round(min(width, height) * 0.085 * scale)))''', '''            # Fit the whole canvas, not an 8.5%-of-window starting font. Tk
            # uses points while the canvas is pixels, so convert only this bound.
            desired_size = max(10, math.ceil(max_height / max(1.0, root.winfo_fpixels("1p"))))''')
    change('''                if max(widths, default=0) > max_width:
                    return None
                glyph_height''', '''                # Keep room for native glyph bearings and the offset shadow.
                shadow = max(1, round(font_size / 20))
                if max(widths, default=0) + (shadow + 4) * 2 > max_width:
                    return None
                glyph_height''')
    change('''            font, font_size, lines, line_height, shadow, safe_x, safe_y = chosen
            text_height''', '''            if chosen is not None and scale < 1.0:
                chosen = candidate(max(10, round(chosen[1] * scale))) or chosen
            font, font_size, lines, line_height, shadow, safe_x, safe_y = chosen
            text_height''')
    change('''            dpi = max(72, widget_dpi(root))
            border = int(state.get("border_pixels", 5) or 5)''', '''            border = int(state.get("border_pixels", 5) or 5)''')
    change('''            desired_points = max(12, min(260, round(min(width, height) * 0.085 * scale)))
            desired_pixels = max(12, round(desired_points * dpi / 72.0))''', '''            # Pillow font sizes and canvas dimensions are both physical pixels.
            # Search the actual available height, without a point-size/DPI cap.
            desired_pixels = max(10, max_height)''')
    change('''            font, emoji_font, lines, widths, line_height, shadow, padding = chosen
            state["artwork_plasma_line_step"]''', '''            if chosen is not None and scale < 1.0:
                chosen = candidate(max(10, round(chosen[0].size * scale))) or chosen
            font, emoji_font, lines, widths, line_height, shadow, padding = chosen
            state["artwork_plasma_line_step"]''')
    compile(source, str(path), 'exec')
    write('PAFPlayer.py', source)


if __name__ == '__main__':
    main()
