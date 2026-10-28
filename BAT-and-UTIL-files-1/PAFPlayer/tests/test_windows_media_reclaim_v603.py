"""Windows media selection regressions without touching the real shell."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import PAFPlayer_windows_media as media


class Controls:
    def __init__(self):
        self.enabled_changes = []
        self.display_updater = SimpleNamespace(music_properties=SimpleNamespace(), update=Mock())
        self.update_timeline_properties = Mock()

    @property
    def is_enabled(self):
        return self.enabled_changes[-1] if self.enabled_changes else False

    @is_enabled.setter
    def is_enabled(self, value):
        self.enabled_changes.append(value)


class ReclaimTests(unittest.TestCase):
    def bridge(self):
        state = {'playing': True, 'paused': False, 'track': {'path': 'first.flac'},
                 'metadata': {'Artist': 'Artist', 'Song': 'First'},
                 'position_seconds': 2, 'duration_seconds': 100}
        server = SimpleNamespace(snapshot=lambda: state, enqueue_action=Mock())
        instance = SimpleNamespace(owns=Mock(return_value=True))
        runtime = SimpleNamespace(settings={'windows_media': dict(media.DEFAULTS, enabled=True, artwork=False)},
                                  server=server, instance=instance, app=SimpleNamespace(WEB_PAUSE='pause'))
        bridge = media.Bridge(runtime)
        controls = Controls()
        bridge.backend = (None, controls, SimpleNamespace(MUSIC=1),
                          SimpleNamespace(PAUSED=1, PLAYING=2, STOPPED=3),
                          SimpleNamespace, None, None, None)
        return bridge, controls, state, instance, server

    def test_play_start_and_track_change_reassert_without_frame_churn(self):
        bridge, controls, state, _, _ = self.bridge()
        with patch.object(media, 'artwork_bytes', return_value=None), \
             patch.object(bridge, 'reclaim_selected_chrome', return_value=False), \
             patch.object(media.time, 'monotonic', side_effect=[10, 11, 12, 13]):
            bridge.tick()
            self.assertEqual([False, True], controls.enabled_changes)
            bridge.tick()
            self.assertEqual([False, True, True], controls.enabled_changes)
            state['track']['path'] = 'second.flac'
            state['metadata']['Song'] = 'Second'
            bridge.tick()
            self.assertEqual([False, True, True, False, True], controls.enabled_changes)
            state['paused'] = True
            bridge.tick()
            self.assertEqual('Paused' if controls.playback_status == 1 else 'wrong', 'Paused')
        self.assertEqual(2, controls.display_updater.update.call_count)

    def test_stopped_and_nonowner_remove_session_and_block_commands(self):
        bridge, controls, state, instance, server = self.bridge()
        with patch.object(media, 'artwork_bytes', return_value=None), \
             patch.object(bridge, 'reclaim_selected_chrome', return_value=False):
            bridge.tick()
            state['transport_stopped'] = True
            bridge.tick()
            self.assertFalse(controls.is_enabled)
            state['transport_stopped'] = False
            instance.owns.return_value = False
            bridge.tick()
            bridge.command('pause')
            self.assertFalse(controls.is_enabled)
            server.enqueue_action.assert_not_called()
            self.assertEqual('Disabled', bridge.status['state'])

    def test_unavailable_session_probe_uses_bounded_reassert(self):
        bridge, controls, _, _, _ = self.bridge()
        def unavailable(*unused):
            bridge.chrome_probe_unavailable = True
            return False
        with patch.object(media, 'artwork_bytes', return_value=None), \
             patch.object(bridge, 'reclaim_selected_chrome', side_effect=unavailable), \
             patch.object(media.time, 'monotonic', side_effect=[0, 29, 31]):
            bridge.tick()
            bridge.tick()
            self.assertEqual(1, controls.enabled_changes.count(False))
            bridge.tick()
            self.assertEqual(2, controls.enabled_changes.count(False))

    def test_selected_chrome_reasserts_even_for_active_video_only_while_music_plays(self):
        bridge, controls, state, _, _ = self.bridge()
        session = SimpleNamespace(source_app_user_model_id='chrome.exe')
        bridge.session_manager = SimpleNamespace(get_current_session=lambda: session)
        self.assertTrue(bridge.reclaim_selected_chrome(controls, state, 100))
        self.assertEqual([False, True], controls.enabled_changes)
        self.assertFalse(bridge.reclaim_selected_chrome(controls, state, 104.9))
        self.assertTrue(bridge.reclaim_selected_chrome(controls, state, 105))
        state['paused'] = True
        self.assertFalse(bridge.reclaim_selected_chrome(controls, state, 110))
        state['paused'] = False
        state['transport_stopped'] = True
        self.assertFalse(bridge.reclaim_selected_chrome(controls, state, 115))
        self.assertEqual([False, True, False, True], controls.enabled_changes)

    def test_non_chrome_session_is_not_reasserted(self):
        bridge, controls, state, _, _ = self.bridge()
        bridge.session_manager = SimpleNamespace(get_current_session=lambda:
            SimpleNamespace(source_app_user_model_id='spotify.exe'))
        self.assertFalse(bridge.reclaim_selected_chrome(controls, state, 100))
        self.assertFalse(controls.enabled_changes)


if __name__ == '__main__':
    unittest.main()
