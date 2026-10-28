import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pafplayer_v550", ROOT / "PAFPlayer.py")
PAF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PAF
SPEC.loader.exec_module(PAF)


class TinyMask:
    size = (3, 2)

    def getpixel(self, point):
        return 255 if point == (1, 0) else 0


def test_floating_hit_test_uses_actual_glyph_pixels_not_crop_rectangle():
    box = [(10, 20, 13, 22)]
    assert PAF.floating_lyric_point_is_clickable(
        11, 20, box, glyph_mask=TinyMask(), glyph_origin=(10, 20)
    )
    assert not PAF.floating_lyric_point_is_clickable(
        10, 20, box, glyph_mask=TinyMask(), glyph_origin=(10, 20)
    )
    assert not PAF.floating_lyric_point_is_clickable(
        12, 21, box, glyph_mask=TinyMask(), glyph_origin=(10, 20)
    )


def test_ctrl_keeps_whole_overlay_interactive_for_editing():
    assert PAF.floating_lyric_point_is_clickable(
        999, 999, [], ctrl_down=True, glyph_mask=TinyMask(), glyph_origin=(10, 20)
    )
