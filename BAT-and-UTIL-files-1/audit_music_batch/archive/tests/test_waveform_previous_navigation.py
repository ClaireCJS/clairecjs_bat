from pathlib import Path
import contextlib
import io
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class WaveformPreviousNavigationTests(unittest.TestCase):
    def test_p_goes_to_previous_and_l_still_listens(self) -> None:
        previewer = mock.Mock(return_value=Path("player.exe"))
        keys = iter(("l", "p"))
        with contextlib.redirect_stdout(io.StringIO()):
            result = audit.waveform_review_choice(
                Path("wave.jpg"), Path("song.flac"), use_color=False,
                key_reader=lambda: next(keys), has_previous=True,
                preview_renderer=lambda *_args, **_kwargs: "preview",
                audio_previewer=previewer,
            )
        self.assertEqual(("previous", 0, Path("song.flac")), result)
        previewer.assert_called_once_with(Path("song.flac"))

    def test_revisiting_replaces_prior_approval_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "01_First.flac"
            second = root / "02_Second.flac"
            first.write_bytes(b"first")
            second.write_bytes(b"second")
            database = root / "approvals.sqlite3"
            decisions = iter(("fine", "previous", "problem", "fine"))
            visited = []

            def generate(_audio, *, destination, **_kwargs):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"test-preview")
                metrics = audit.WaveformMetrics(
                    channel_peak_percentages=(50.0,), peak_volume_percentage=50.0,
                    average_volume_percentage=25.0, replaygain_factor=None,
                    longest_silence_seconds=0.0, total_silence_seconds=0.0,
                )
                return destination, None, metrics

            def review(_waveform, audio, **options):
                visited.append((audio.name, options["has_previous"]))
                return next(decisions), 0, audio

            with mock.patch.object(audit, "generate_waveform_jpeg", side_effect=generate), \
                 mock.patch.object(audit, "ensure_waveform_jpeg_ready"), \
                 mock.patch.object(audit, "replaygain_bake_candidates", return_value=[]), \
                 mock.patch.object(audit, "waveform_review_choice", side_effect=review), \
                 mock.patch.object(audit, "waveform_staging_root", return_value=root), \
                 contextlib.redirect_stdout(io.StringIO()):
                result = audit.review_waveforms(
                    root, use_color=False, workers=1,
                    preview_renderer=lambda *_args, **_kwargs: "preview",
                    approval_database_path=database,
                )
            self.assertEqual(
                [("01_First.flac", False), ("02_Second.flac", True),
                 ("01_First.flac", False), ("02_Second.flac", True)],
                visited,
            )
            self.assertEqual([str(second)], result["fine"])
            self.assertEqual([str(first)], [item["path"] for item in result["problems"]])
            store = audit.WaveformApprovalStore(database)
            self.assertFalse(store.is_approved(first))
            self.assertTrue(store.is_approved(second))


if __name__ == "__main__":
    unittest.main()
