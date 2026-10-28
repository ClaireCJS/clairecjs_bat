"""Focused browser lyric preview regressions for V502."""

import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import PAFPlayer as app


class ProgressLyricTooltipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = app._paf_web_html()
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", cls.html, re.S)
        cls.javascript = "\n".join(scripts)
        start = cls.javascript.index("function progressLyricTimeAt(")
        end = cls.javascript.index("const progressHost=", start)
        cls.preview_functions = cls.javascript[start:end]

    def test_preview_uses_current_cue_and_fades_last_cue_for_five_seconds(self):
        scenario = r"""
const timeline=[[0,''],[2,'first'],[4,''],[12,'second'],[16,'']];
const positions=[0,1.99,2,3.99,4,8.999,9,9.001,11,12,16,21,21.001];
console.log(JSON.stringify(positions.map(position=>progressLyricPreviewAt(timeline,position))));
"""
        result = subprocess.run(
            ["node", "-e", self.preview_functions + scenario],
            text=True, encoding="utf-8", capture_output=True, check=True,
        )
        values = json.loads(result.stdout)
        blank = {"text": "", "faded": False}
        current_first = {"text": "first", "faded": False}
        faded_first = {"text": "first", "faded": True}
        self.assertEqual(
            [blank, blank, current_first, current_first, faded_first, faded_first,
             faded_first, blank, blank, {"text": "second", "faded": False},
             {"text": "second", "faded": True}, {"text": "second", "faded": True}, blank],
            values,
        )

    def test_hover_time_uses_playback_start_and_karaoke_offsets(self):
        scenario = r"""
console.log(JSON.stringify([
  progressLyricTimeAt(.5,60,{position:10,lyricPosition:20,karaokeOffset:-2}),
  progressLyricTimeAt(0,60,{position:0,lyricPosition:0,karaokeOffset:-2}),
  progressLyricTimeAt(2,60,{position:10,lyricPosition:20,karaokeOffset:0})
]));
"""
        result = subprocess.run(
            ["node", "-e", self.preview_functions + scenario],
            text=True, encoding="utf-8", capture_output=True, check=True,
        )
        self.assertEqual([38, 0, 70], json.loads(result.stdout))

    def test_hover_ui_is_visible_unclipped_and_seek_click_is_preserved(self):
        html = self.html
        self.assertIn('id="progressLyricTooltip" role="tooltip" hidden', html)
        self.assertIn("#progressLyricTooltip .preview-lyric.faded{opacity:.5}", html)
        self.assertIn("position:fixed;z-index:90;pointer-events:none", html)
        self.assertIn("progressHost.addEventListener('pointermove',showProgressLyricTooltip)", html)
        self.assertIn("progressHost.addEventListener('pointerleave',hideProgressLyricTooltip)", html)
        self.assertIn("lyric.textContent=preview.text||''", html)
        self.assertIn("action('web-seek-ratio:'+ratio.toFixed(6))", html)

    def test_complete_web_javascript_parses(self):
        result = subprocess.run(
            ["node", "--check"], input=self.javascript, text=True,
            encoding="utf-8", capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
