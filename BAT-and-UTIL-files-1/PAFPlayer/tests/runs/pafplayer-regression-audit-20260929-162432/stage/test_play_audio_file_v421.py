"""Manual control and source-scoped automatic interruptions."""
import unittest
import play_audio_file as p
from test_play_audio_file_v420 import Monitor


class OverrideTests(unittest.TestCase):
    def setUp(self):
        self.monitor = Monitor()
        self.player = p.PAFExternalPlaybackCoordinator(self.monitor)

    def tick(self, at, active, paused=False, action=None, known=True):
        self.monitor.value = {'active': active, 'known': known}
        return self.player.filter_action(action, paused, at)

    def test_existing_background_media_does_not_pause_startup(self):
        self.assertIsNone(self.tick(0, ('chrome', 'VLC')))
        self.assertIsNone(self.tick(10, ('chrome', 'VLC')))
        self.assertEqual(['VLC', 'chrome'], self.player.status()['external_media_acknowledged'])
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.tick(11, ('chrome', 'VLC', 'Winamp')))

    def test_delayed_initial_monitor_sample_is_background_baseline(self):
        self.tick(0, (), known=False)
        self.assertEqual(p.WEB_PLAY, self.tick(1, (), True, p.WEB_PLAY, known=False))
        self.assertIsNone(self.tick(2, ('chrome',)))
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.tick(3, ('chrome', 'VLC')))

    def test_play_and_space_always_release_hold_without_immediate_repause(self):
        for action in (p.WEB_PLAY, p.PAUSE_TOGGLE):
            with self.subTest(action=action):
                self.setUp()
                self.tick(0, ())
                self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.tick(1, ('chrome',)))
                self.assertEqual(action, self.tick(2, ('chrome',), True, action))
                self.assertFalse(self.player.auto_paused)
                self.assertIsNone(self.tick(3, ('chrome',)))
                self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.tick(4, ('chrome', 'VLC')))

    def test_new_vlc_finishes_and_resumes_despite_acknowledged_chrome(self):
        self.tick(0, ('chrome',))
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.tick(1, ('chrome', 'VLC')))
        self.assertIsNone(self.tick(2, ('chrome',), True))
        self.assertEqual(p.EXTERNAL_MEDIA_RESUME, self.tick(4, ('chrome',), True))
        self.assertEqual((15, 0), self.player.fade_arguments())

    def test_source_rearms_independently_while_other_background_media_continues(self):
        self.tick(0, ('chrome', 'VLC'))
        self.tick(1, ('chrome',))
        self.tick(3, ('chrome',))
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.tick(4, ('chrome', 'VLC')))

    def test_short_gap_or_unknown_monitor_does_not_erase_override(self):
        self.tick(0, ('chrome',))
        self.tick(1, ())
        self.assertIsNone(self.tick(2, ('chrome',)))
        self.tick(3, (), known=False)
        self.assertIsNone(self.tick(100, ('chrome',)))

    def test_unknown_monitor_never_blocks_manual_play(self):
        self.tick(0, ())
        self.tick(1, ('VLC',))
        self.assertEqual(p.WEB_PLAY, self.tick(2, (), True, p.WEB_PLAY, known=False))
        self.assertFalse(self.player.auto_paused)
        self.assertIsNone(self.tick(3, ("VLC",)))

    def test_manual_pause_remains_held_after_new_media_finishes(self):
        self.tick(0, ())
        self.tick(1, ('VLC',))
        self.tick(2, ('VLC',), True, p.WEB_PAUSE)
        self.tick(3, (), True)
        self.assertIsNone(self.tick(10, (), True))


if __name__ == '__main__': unittest.main()
