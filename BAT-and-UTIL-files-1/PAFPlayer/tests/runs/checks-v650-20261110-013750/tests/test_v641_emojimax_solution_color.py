"""Web and floating Emojimaxx solution colors follow their visible controls."""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import unittest

from PIL import Image

import PAFPlayer as app


class NativeSolutionColorTests(unittest.TestCase):
    def setUp(self):
        self.rgba = Image.new("RGBA", (8, 4), (0, 0, 0, 0))
        self.mask = Image.new("L", (8, 4), 0)
        # A fully opaque black shadow must not win over the actual glyph.
        self.rgba.putpixel((0, 1), (0, 0, 0, 255))
        self.rgba.putpixel((2, 1), (15, 100, 230, 255))
        self.mask.putpixel((2, 1), 255)

    def test_fixed_color_ignores_animated_lyric_pixels(self):
        self.assertEqual("#aabbcc", app.emojimax_solution_label_color(
            "#aabbcc", False, (0, 0, 8, 4), self.rgba, (0, 0), self.mask))

    def test_inherited_color_uses_first_solid_glyph_not_shadow(self):
        self.assertEqual("#0f64e6", app.emojimax_solution_label_color(
            "#aabbcc", True, (0, 0, 8, 4), self.rgba, (0, 0), self.mask))
        self.rgba.putpixel((2, 1), (240, 30, 90, 255))
        self.assertEqual("#f01e5a", app.emojimax_solution_label_color(
            "#aabbcc", True, (0, 0, 8, 4), self.rgba, (0, 0), self.mask))

    def test_no_glyph_pixel_uses_configured_color(self):
        self.assertEqual("#aabbcc", app.emojimax_solution_label_color(
            "#aabbcc", True, (20, 20, 30, 30), self.rgba, (0, 0), self.mask))


class WebSolutionColorTests(unittest.TestCase):
    def test_web_fixed_and_inherited_color_rules(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("WARNING: Node.js unavailable for web color rule check")
        source = (Path(__file__).resolve().parents[1] / "PAFPlayer.py").read_text(encoding="utf-8")
        match = re.search(r"function webEmojimaxSolutionColor\([^\n]+", source)
        self.assertIsNotNone(match)
        script = (match.group(0) + "\n" +
                  "const assert=require('node:assert/strict');" +
                  "assert.equal(webEmojimaxSolutionColor('rgb(1, 2, 3)',false,'#aabbcc'),'#aabbcc');" +
                  "assert.equal(webEmojimaxSolutionColor('rgb(1, 2, 3)',true,'#aabbcc'),'rgb(1, 2, 3)');" +
                  "assert.equal(webEmojimaxSolutionColor('red',false,'bad'),'#f4f8ff');")
        result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("tip.style.color=currentWebEmojimaxSolutionColor(span)", source)
        self.assertIn("source_rgba=rgba, source_origin=origin, source_mask=mask", source)


if __name__ == "__main__":
    unittest.main()
