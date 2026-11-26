import ast,inspect,unittest
from unittest.mock import patch
import PAFPlayer as app
import PAFPlayer_instance as instances

class PauseOwnershipTests(unittest.TestCase):
    def test_simple_yields_to_another_player(self):
        with patch.object(app,'_SIMPLE_INLINE_CONSOLE',True),patch.object(instances,'other_player_running',return_value=True):
            self.assertFalse(app.global_pause_hotkey_allowed())

    def test_simple_responds_when_alone(self):
        with patch.object(app,'_SIMPLE_INLINE_CONSOLE',True),patch.object(instances,'other_player_running',return_value=False):
            self.assertTrue(app.global_pause_hotkey_allowed())

    def test_normal_player_does_not_scan_or_yield(self):
        with patch.object(app,'_SIMPLE_INLINE_CONSOLE',False),patch.object(instances,'other_player_running') as scan:
            self.assertTrue(app.global_pause_hotkey_allowed());scan.assert_not_called()

    def test_space_is_still_a_focused_pause_control(self):
        self.assertEqual(app.interpret_console_key(' '),app.PAUSE_TOGGLE)

    def test_win_c_and_both_media_polling_paths_are_gated(self):
        text=inspect.getsource(app.read_windows_key_action)
        self.assertIn('if global_pause_hotkey_allowed(): return PAUSE_TOGGLE',text)
        self.assertIn('if media_action != PAUSE_TOGGLE or global_pause_hotkey_allowed(): return media_action',text)
        self.assertIn('if action != PAUSE_TOGGLE or global_pause_hotkey_allowed(): return action',text)
