from pathlib import Path
import inspect
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import PAFPlayer as paf


class V653IdleArtworkMusicDanceTests(unittest.TestCase):
    def test_music_step_uses_bounded_progress_pulse(self):
        self.assertEqual(1, paf.external_album_art_music_dance_step(0.0, False))
        self.assertEqual(0, paf.external_album_art_music_dance_step(0.0, True))
        self.assertEqual(6, paf.external_album_art_music_dance_step(0.5, True))
        self.assertEqual(12, paf.external_album_art_music_dance_step(1.0, True))
        self.assertEqual(12, paf.external_album_art_music_dance_step(99.0, True))

    def test_checkbox_is_experimental_persistent_and_web_settable(self):
        toggles = {item["key"]: item for item in paf.paf_web_control_schema()["toggles"]}
        item = toggles["idle_artwork_dance_to_music"]
        self.assertEqual("Dance to music", item["label"])
        self.assertTrue(item["experimental"])
        self.assertEqual(0, paf.PLAYER_SETTING_DEFAULTS["ExternalAlbumArtIdleDanceToMusic"])
        self.assertTrue(paf.paf_web_action_is_allowed("web-set:idle_artwork_dance_to_music:1"))

    def test_artwork_consumes_progress_bar_beat_value_without_analyzer(self):
        playback = inspect.getsource(paf.play_audio_file)
        artwork = inspect.getsource(paf.ExternalAlbumArtWindow)
        self.assertIn("update_idle_dance_music_pulse(progress_beat_value)", playback)
        self.assertIn("external_album_art_music_dance_step(pulse, enabled)", artwork)
        self.assertNotIn("progress_beat_pulse(", inspect.getsource(paf.ExternalAlbumArtWindow.update_idle_dance_music_pulse))

    def test_stale_music_pulse_stops_music_driven_motion(self):
        window = paf.ExternalAlbumArtWindow(enabled=False, idle_dance_to_music=True)
        window.update_idle_dance_music_pulse(1.0, at=10.0)
        self.assertEqual(12, window._idle_dance_step(10.1))
        self.assertEqual(0, window._idle_dance_step(10.5))


if __name__ == "__main__":
    unittest.main()
