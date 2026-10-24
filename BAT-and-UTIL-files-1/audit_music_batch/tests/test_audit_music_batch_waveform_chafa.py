from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class DirectWaveformChafaTests(unittest.TestCase):
    def setUp(self) -> None:
        if audit.Image is None:
            self.skipTest("Pillow is required")
        self.geometry = audit.ArtworkPreviewGeometry(
            terminal_columns=200,
            terminal_rows=44,
            indent_columns=0,
            columns=200,
            rows=44,
            pixel_width=2000,
            pixel_height=880,
        )

    def make_waveform(self, folder: str) -> Path:
        path = Path(folder) / "waveform.jpg"
        audit.Image.new("RGB", (2000, 700), (210, 35, 145)).save(
            path,
            format="JPEG",
            quality=95,
        )
        return path

    def test_single_and_pair_use_echo_image_viewports(self) -> None:
        module = audit
        with tempfile.TemporaryDirectory() as folder:
            waveform = self.make_waveform(folder)
            with mock.patch.object(
                module,
                "artwork_preview_geometry",
                return_value=self.geometry,
            ):
                single = module.prepare_waveform_preview(
                    waveform,
                    use_color=True,
                    width_fraction=0.72,
                    height_scale=0.72,
                )
                pair = module.prepare_waveform_preview(
                    waveform,
                    use_color=True,
                    width_fraction=0.72,
                    height_scale=0.36,
                )

        self.assertEqual("direct Chafa 1.18.2 Sixel", single.mode)
        self.assertIn("--view-size=144x32", single.direct_command)
        self.assertIn("--view-size=144x16", pair.direct_command)
        for prepared in (single, pair):
            command = prepared.direct_command
            self.assertIn("--format=sixels", command)
            self.assertIn("--colors=full", command)
            self.assertIn("--scale=max", command)
            self.assertIn("--optimize=9", command)
            self.assertIn("--work=9", command)
            self.assertIn("--color-space=din99d", command)
            self.assertIn("--margin-bottom=4", command)
            self.assertIn("--margin-right=0", command)
            self.assertNotIn("--stretch", command)
            self.assertFalse(any(part.startswith("--size=") for part in command))

    def test_emitter_gives_chafa_the_live_terminal(self) -> None:
        command = (r"C:\util\chafa-1.18.2.exe", "--format=sixels", "wave.jpg")
        prepared = audit.PreparedArtworkPreview(
            mode="direct Chafa 1.18.2 Sixel",
            geometry=self.geometry,
            direct_command=command,
        )
        completed = subprocess.CompletedProcess(command, 0)
        raw_terminal = object()
        with mock.patch.object(
            audit.subprocess,
            "run",
            return_value=completed,
        ) as run, mock.patch.object(
            audit,
            "_raw_console_stream",
            return_value=raw_terminal,
        ):
            audit.emit_prepared_artwork_preview(prepared)
        run.assert_called_once_with(
            list(command),
            stdout=raw_terminal,
            check=False,
        )
        kwargs = run.call_args.kwargs
        self.assertNotIn("stderr", kwargs)

    def test_real_chafa_produces_a_multirow_sixel_raster(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            waveform = self.make_waveform(folder)
            with mock.patch.object(
                audit,
                "artwork_preview_geometry",
                return_value=self.geometry,
            ):
                prepared = audit.prepare_waveform_preview(
                    waveform,
                    use_color=True,
                    width_fraction=0.72,
                    height_scale=0.72,
                )
            result = subprocess.run(
                list(prepared.direct_command),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr.decode(errors="replace"))
        raster = audit.sixel_payload_pixel_size(result.stdout)
        self.assertIsNotNone(raster)
        _width, height = raster or (0, 0)
        self.assertGreater(height, 20, "Chafa emitted only a one-text-row raster")

    def test_artwork_preview_uses_direct_echo_image_chafa_contract(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            artwork = self.make_waveform(folder)
            with mock.patch.object(
                audit,
                "artwork_preview_geometry",
                return_value=self.geometry,
            ), mock.patch.object(
                audit,
                "terminal_supports_sixel",
                return_value=True,
            ):
                prepared = audit.prepare_artwork_preview(
                    artwork,
                    use_color=True,
                    prefer_sixel=True,
                )
        self.assertEqual("Chafa Sixel", prepared.mode)
        self.assertTrue(prepared.direct_command)
        command = prepared.direct_command
        self.assertIn("--format=sixels", command)
        self.assertIn("--colors=full", command)
        self.assertIn("--view-size=200x44", command)
        self.assertIn("--scale=max", command)
        self.assertIn("--optimize=9", command)
        self.assertIn("--work=9", command)
        self.assertIn("--color-space=din99d", command)
        self.assertIn("--margin-bottom=4", command)
        self.assertIn("--margin-right=0", command)


if __name__ == "__main__":
    unittest.main(verbosity=2)
