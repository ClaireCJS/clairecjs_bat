"""The next track's expensive setup is warmed off the playback path."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import PAFPlayer as player


class TransitionPrefetchTests(unittest.TestCase):
    def test_cover_render_is_reused_at_track_handoff(self):
        with tempfile.TemporaryDirectory() as raw:
            audio = Path(raw) / 'next.flac'
            audio.write_bytes(b'FLAC')
            with patch.object(player, '_render_preplay_album_cover_uncached', return_value=b'sixel') as render:
                self.assertEqual(b'sixel', player.render_preplay_album_cover(audio, 130))
                self.assertEqual(b'sixel', player.render_preplay_album_cover(audio, 130))
                render.assert_called_once_with(audio, 130)

    def test_successor_prefetch_uses_playback_probe_contract(self):
        with tempfile.TemporaryDirectory() as raw:
            audio = Path(raw) / 'next.flac'
            audio.write_bytes(b'FLAC')
            with patch.object(player, 'probe_duration_seconds', return_value=120.0) as duration, \
                 patch.object(player, 'probe_audio_tags') as tags, \
                 patch.object(player, 'replaygain_info_for_audio') as gain, \
                 patch.object(player, 'detect_edge_silence_bounds') as silence, \
                 patch.object(player, 'render_preplay_album_cover') as art:
                player.prefetch_playlist_successor(
                    audio, replaygain_mode='track', trim_edge_silence=True,
                    threshold_db=-45, min_duration=.5, keep_seconds=.1,
                    cover_columns=140)
                duration.assert_called_once_with(audio)
                tags.assert_called_once_with(audio)
                gain.assert_called_once_with(audio, 'track')
                silence.assert_called_once_with(audio, 120.0, enabled=True,
                                                threshold_db=-45, min_duration=.5,
                                                keep_seconds=.1)
                art.assert_called_once_with(audio, 140)


if __name__ == '__main__':
    unittest.main()
