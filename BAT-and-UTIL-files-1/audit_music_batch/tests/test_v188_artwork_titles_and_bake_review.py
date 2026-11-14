from pathlib import Path
import contextlib
import io
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class V188ArtworkTitlesAndBakeReviewTests(unittest.TestCase):
    def test_youtube_rip_filename_prefers_its_video_thumbnail(self) -> None:
        path = Path(
            "Steve Welsh - Endless Nameless (youtube-rip) (TURlIQPRks8).flac"
        )
        match = audit.youtube_thumbnail_cover_match(path)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual("YouTube thumbnail", match.source)
        self.assertEqual("TURlIQPRks8", match.release_id)
        self.assertEqual(
            "https://i.ytimg.com/vi/TURlIQPRks8/maxresdefault.jpg",
            match.artworks[0].url,
        )

    def test_youtube_match_precedes_release_database_requests(self) -> None:
        path = Path("Song (youtube-rip) (TURlIQPRks8).flac")
        fetcher = mock.Mock(side_effect=AssertionError("database was queried"))
        match = audit.resolve_cover_match(path, json_fetcher=fetcher)
        self.assertEqual("YouTube thumbnail", match.source)
        fetcher.assert_not_called()

    def test_common_apostrophes_use_ascii_in_filenames_and_curly_in_tags(self) -> None:
        self.assertEqual(
            "01_I'm Here And You Don't Know.flac",
            audit.canonicalized_filename("01_Im Here And You Dont Know.flac"),
        )
        self.assertEqual(
            "I’m Here And You Don’t Know",
            audit.repair_common_missing_apostrophes(
                "Im Here And You Dont Know", curly=True
            ),
        )
        self.assertEqual(
            "Its A Fine Day",
            audit.repair_common_missing_apostrophes("Its A Fine Day", curly=True),
        )

    def test_bake_prompt_w_renders_one_candidate_then_returns_to_choice(self) -> None:
        metrics = audit.WaveformMetrics((80.0, 75.0), 80.0, 40.0, 0.5, 1.0, 2.0)
        with tempfile.TemporaryDirectory() as directory:
            waveform = Path(directory) / "waveform.jpg"
            waveform.write_bytes(b"jpeg")
            keys = iter(("w", "n"))
            with mock.patch.object(
                audit,
                "generate_waveform_jpeg",
                return_value=(waveform, None, metrics),
            ) as generate, mock.patch.object(
                audit, "recolor_before_baked_waveform"
            ), mock.patch.object(
                audit, "render_waveform_preview", return_value="sixel"
            ) as render, contextlib.redirect_stdout(io.StringIO()):
                accepted = audit.prompt_for_replaygain_batch_bake(
                    [Path("one.flac")],
                    threshold_text="±0.05 dB",
                    use_color=False,
                    key_reader=lambda: next(keys),
                )
        self.assertFalse(accepted)
        generate.assert_called_once()
        render.assert_called_once_with(waveform, use_color=False)

    def test_all_caps_label_describes_track_not_album(self) -> None:
        self.assertEqual(
            "All-caps track title",
            audit.friendly_category("all_caps_album_title"),
        )
        self.assertIn(
            "track title",
            audit.ACTION_PROMPT_QUESTIONS["all_caps_album_title"],
        )


if __name__ == "__main__":
    unittest.main()
