import inspect
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import PAFPlayer as app


class TestToneV542(unittest.TestCase):
    def setUp(self):
        app._TEST_TONE_STATE.update(enabled=False, selected=0,
                                    tones=[{"frequency": 440.0, "pattern": 0, "volume": 20}],
                                    processes=[], output=(2, 48000, -1, 16))

    def test_ctrl_t_and_mode_navigation_keys(self):
        self.assertEqual(app.TEST_TONE_TOGGLE, app.interpret_console_key("\x14", ctrl=True))
        app._TEST_TONE_STATE["enabled"] = True
        self.assertEqual(app.TEST_TONE_FREQUENCY_DOWN, app.interpret_console_key("\x00", extended="K"))
        self.assertEqual(app.TEST_TONE_FREQUENCY_UP, app.interpret_console_key("\x00", extended="M"))
        self.assertEqual(app.TEST_TONE_PATTERN_NEXT, app.interpret_console_key("\x00", extended="H"))
        self.assertEqual(app.TEST_TONE_PATTERN_PREVIOUS, app.interpret_console_key("\x00", extended="P"))
        self.assertEqual(app.TEST_TONE_SELECT_NEXT, app.interpret_console_key("T", shift=True))
        self.assertEqual(app.TEST_TONE_ADD, app.interpret_console_key("t", alt=True))
        self.assertEqual(app.TEST_TONE_SAVE, app.interpret_console_key("\x13", ctrl=True))
        self.assertEqual(app.TEST_TONE_LOAD, app.interpret_console_key("\x0c", ctrl=True))

    def test_unbounded_tones_and_independent_edits(self):
        with mock.patch.object(app, "_restart_test_tones"):
            for _ in range(40):
                app.test_tone_operation("add")
            self.assertEqual(41, len(app.test_tone_snapshot()["tones"]))
            app.test_tone_operation("update", index=20, frequency=1234, pattern=3, volume=17)
        tones = app.test_tone_snapshot()["tones"]
        self.assertEqual({"frequency": 1234.0, "pattern": 3, "volume": 17}, tones[20])
        self.assertEqual(440.0, tones[0]["frequency"])

    def test_patterns_are_distinct_and_bounded(self):
        expressions = {app._test_tone_expression({"frequency": 440, "pattern": i, "volume": 20})
                       for i in range(len(app.TEST_TONE_PATTERNS))}
        self.assertEqual(5, len(expressions))
        with mock.patch.object(app, "_restart_test_tones"):
            app.test_tone_operation("update", frequency=1, volume=999)
        tone = app.test_tone_snapshot()["tones"][0]
        self.assertEqual(20.0, tone["frequency"])
        self.assertEqual(50, tone["volume"])

    def test_ffmpeg_accepts_every_pattern(self):
        ffmpeg = app.direct_ffmpeg_executable()
        if ffmpeg is None:
            self.skipTest("native ffmpeg unavailable")
        for pattern in range(len(app.TEST_TONE_PATTERNS)):
            expression = app._test_tone_expression({"frequency": 440, "pattern": pattern, "volume": 10})
            result = subprocess.run([str(ffmpeg), "-v", "error", "-f", "lavfi", "-t", "0.02", "-i",
                                     "aevalsrc=" + expression + ":s=48000:c=mono",
                                     "-f", "null", "-"], capture_output=True, timeout=10)
            self.assertEqual(0, result.returncode, result.stderr.decode(errors="replace"))

    def test_named_set_round_trip(self):
        store = {}
        def read(_name, fallback): return dict(store) if store else fallback
        def write(_name, value): store.clear(); store.update(value)
        with mock.patch.object(app, "_restart_test_tones"), \
             mock.patch.object(app, "_read_registry_json_string", side_effect=read), \
             mock.patch.object(app, "_write_registry_json_string", side_effect=write):
            app.test_tone_operation("update", frequency=880, pattern=2, volume=12)
            app.test_tone_operation("save", set_name="Octaves", description="Octaves")
            app.test_tone_operation("update", frequency=220)
            app.test_tone_operation("load", set_name="Octaves")
            self.assertEqual(880.0, app.test_tone_snapshot()["tones"][0]["frequency"])

    def test_web_and_native_contract_present(self):
        source = (ROOT / "PAFPlayer.py").read_text(encoding="utf-8-sig")
        for text in ('id="matrixTestToneEnabled"', '/api/test-tone', 'matrixTonePost',
                     'TestToneSetsV542', 'PROGRAM_VERSION                 = "V542"'):
            self.assertIn(text, source)
        reader = inspect.getsource(app.read_windows_key_action)
        self.assertIn('0x01, TEST_TONE_FREQUENCY_DOWN', reader)
        self.assertIn('return TEST_TONE_ADD', reader)


if __name__ == "__main__":
    unittest.main()
