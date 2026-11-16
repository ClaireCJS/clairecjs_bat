import importlib.util
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('v658_dj_source', ROOT / 'src/PAFPlayer_dj.py')
dj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dj)
spec = importlib.util.spec_from_file_location('v658_player', ROOT / 'PAFPlayer.py')
player = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = player
spec.loader.exec_module(player)


class DJHelpTests(unittest.TestCase):
    def runtime(self):
        return SimpleNamespace(settings={}, lock=threading.RLock(),
                               stop_event=threading.Event(), save_settings=lambda: None)

    def test_dialogue_survives_speech_failure_and_is_visible(self):
        controller = dj.Controller(self.runtime())
        controller.configure({'speech_provider': 'piper', 'piper_executable': '', 'piper_voices': ''})
        with mock.patch.object(dj, 'dialogue', return_value=([(1, 'A little introduction.'), (2, 'Hello!')], '')), mock.patch.object(dj.shutil, 'which', return_value=None), mock.patch.object(dj, 'ensure_piper', side_effect=RuntimeError('unavailable')):
            self.assertTrue(controller.start(True, current={'artist': 'A', 'title': 'B'}))
            deadline = time.monotonic() + 3
            while controller.working is not None and time.monotonic() < deadline:
                time.sleep(.005)
        lines = player.dj_help_rows(controller, 80)
        self.assertIn('Speaker 1: A little introduction.', lines)
        self.assertIn('Speaker 2: Hello!', lines)
        self.assertIn('DJ speech failed', ' '.join(lines))
        self.assertFalse(controller.due())

    def test_help_sanitizes_control_sequences_and_wraps(self):
        controller = SimpleNamespace(help_snapshot=lambda: (((1, 'hello\x1b[31m world ' * 4),), 'Ready', '', '', True))
        rows = player.dj_help_rows(controller, 20)
        self.assertNotIn('\x1b', ''.join(rows))
        self.assertTrue(all(player.terminal_cell_width(row) <= 20 for row in rows))
        self.assertGreater(len(rows), 2)

    def test_cancelled_generation_never_publishes_text(self):
        controller = dj.Controller(self.runtime())
        entered, release = threading.Event(), threading.Event()
        def dialogue(*args):
            entered.set(); release.wait(2)
            return [(1, 'Stale text')], ''
        with mock.patch.object(dj, 'dialogue', side_effect=dialogue):
            controller.start(True, current={'artist': 'A', 'title': 'B'})
            self.assertTrue(entered.wait(1))
            controller.cancel_request(); release.set()
            deadline = time.monotonic() + 2
            while controller.working is not None and time.monotonic() < deadline:
                time.sleep(.005)
        self.assertEqual((), controller.help_snapshot()[0])


if __name__ == '__main__':
    unittest.main()
