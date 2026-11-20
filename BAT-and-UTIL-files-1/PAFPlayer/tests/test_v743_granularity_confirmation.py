"""Exercise both explicit granularity confirmations without touching a console."""
import ast
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'PAFPlayer.py'
TREE = ast.parse(SOURCE.read_text(encoding='utf-8'))
NODE = next(n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == 'confirm_console_granularity')
CODE = compile(ast.fix_missing_locations(ast.Module(body=[NODE], type_ignores=[])), str(SOURCE), 'exec')

class ConfirmationTests(unittest.TestCase):
    def run_prompt(self, keys, pump=True):
        queue = deque(keys)
        screen = []
        fake = SimpleNamespace(kbhit=lambda: bool(queue), getwch=queue.popleft)
        clock = iter(range(100))
        scope = {'os': SimpleNamespace(name='nt'), 'monotonic': lambda: next(clock),
                 'render_catalog_prompt': screen.append, 'pump_prompt_visualizer': lambda: pump,
                 'sleeper': lambda _: None}
        with mock.patch.dict('sys.modules', {'msvcrt': fake}):
            exec(CODE, scope)
            result = scope['confirm_console_granularity']('Shift+F4')
        return result, screen

    def test_requires_two_different_confirmations_and_names_key(self):
        result, screens = self.run_prompt('yyc')
        self.assertTrue(result)
        self.assertEqual(2, len(screens))
        self.assertTrue(all('Shift+F4' in '\n'.join(screen) for screen in screens))
        self.assertIn('Press Y', '\n'.join(screens[0]))
        self.assertIn('Press C', '\n'.join(screens[1]))

    def test_cancel_at_either_stage(self):
        for keys in ('n', '\x1b', 'yn', 'y\x1b'):
            with self.subTest(keys=keys):
                self.assertFalse(self.run_prompt(keys)[0])

    def test_repeat_and_timeout_do_not_confirm(self):
        self.assertFalse(self.run_prompt('yyyyy')[0])
        self.assertFalse(self.run_prompt('c')[0])

    def test_abort_or_end_of_playback_cancels(self):
        self.assertFalse(self.run_prompt('yc', pump=False)[0])

if __name__ == '__main__':
    unittest.main()