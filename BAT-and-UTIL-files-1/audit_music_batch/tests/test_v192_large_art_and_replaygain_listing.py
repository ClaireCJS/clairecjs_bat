from pathlib import Path
import contextlib
import hashlib
import io
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class V192LargeArtAndReplayGainListingTests(unittest.TestCase):
    def test_oversized_cover_is_recompressed_without_changing_sidecar(self) -> None:
        if audit.Image is None:
            self.skipTest("Pillow is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            cover = Path(directory) / "cover.jpg"
            image = audit.Image.effect_noise((900, 900), 100).convert("RGB")
            image.save(cover, format="JPEG", quality=100, subsampling=0)
            before = cover.read_bytes()
            before_hash = hashlib.sha256(before).digest()

            with mock.patch.object(
                audit, "FLAC_EMBEDDED_ART_TARGET_BYTES", 100_000
            ):
                payload, mime, optimized = audit.flac_embeddable_art_payload(
                    cover
                )

            self.assertTrue(optimized)
            self.assertEqual("image/jpeg", mime)
            self.assertLessEqual(len(payload), 100_000)
            self.assertEqual(before_hash, hashlib.sha256(cover.read_bytes()).digest())

    def test_replaygain_folder_prompt_accepts_list_key(self) -> None:
        prompt = audit.action_scope_prompt(
            "Run ReplayGain on this folder now?",
            default_yes=True,
            use_color=False,
            allow_list_files=True,
        )
        self.assertIn("L=List Files + Metrics", prompt)
        with contextlib.redirect_stdout(io.StringIO()):
            choice = audit.prompt_for_action_scope(
                "Run ReplayGain on this folder now?",
                default_yes=True,
                use_color=False,
                key_reader=lambda: "l",
                allow_list_files=True,
            )
        self.assertEqual("list_files", choice)

    def test_replaygain_listing_includes_graph_metrics_and_tag_adjustment(self) -> None:
        path = Path(r"C:\Music\Track.flac")
        metrics = audit.WaveformMetrics(
            channel_peak_percentages=(90.0, 88.0),
            peak_volume_percentage=90.0,
            average_volume_percentage=25.0,
            replaygain_factor=1.0,
            longest_silence_seconds=1.5,
            total_silence_seconds=3.0,
        )
        with mock.patch.object(
            audit, "measure_waveform_metrics", return_value=metrics
        ), mock.patch.object(
            audit, "waveform_replaygain_factor", return_value=0.5
        ), contextlib.redirect_stdout(io.StringIO()) as output:
            audit.print_replaygain_files_with_metrics([path])
        rendered = output.getvalue()
        self.assertIn(str(path), rendered)
        self.assertIn("tagged adjustment:", rendered)
        self.assertIn("peak vol:", rendered)
        self.assertIn("silence:", rendered)


if __name__ == "__main__":
    unittest.main()
