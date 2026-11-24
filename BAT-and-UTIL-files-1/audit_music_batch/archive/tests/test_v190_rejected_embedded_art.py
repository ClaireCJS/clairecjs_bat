from pathlib import Path
import contextlib
import io
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class V190RejectedEmbeddedArtworkTests(unittest.TestCase):
    def test_remove_prompt_has_no_enter_default(self) -> None:
        keys = iter(("\r", "y"))
        with mock.patch.object(audit, "invalid_key_beep") as beep, \
             contextlib.redirect_stdout(io.StringIO()):
            accepted = audit.prompt_remove_rejected_embedded_art(
                Path("Song.flac"),
                use_color=False,
                key_reader=lambda: next(keys),
            )
        self.assertTrue(accepted)
        beep.assert_called_once()

    def test_rejected_sidecar_yes_removes_embedded_art(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "Song.flac"
            audio.write_bytes(b"audio")
            sidecar = root / "Song.jpg"
            sidecar.write_bytes(b"image")
            actions = [f"exported_art:{sidecar}"]

            def recycle(path: Path) -> Path:
                self.assertTrue(Path(path).name.endswith(".rejected-by-username.jpg"))
                return Path(path)

            with mock.patch.object(
                audit, "artwork_review_choice", return_value=False
            ), mock.patch.object(
                audit, "recycle_path", side_effect=recycle
            ), mock.patch.object(
                audit,
                "remove_embedded_artwork",
                return_value=["backup:audio.bak", f"removed_embedded_art:{audio}"],
            ) as remove, contextlib.redirect_stdout(io.StringIO()):
                approved = audit.review_extracted_art_sidecars(
                    actions,
                    use_color=False,
                    key_reader=lambda: "y",
                    audio_path=audio,
                )
        self.assertFalse(approved)
        remove.assert_called_once_with(audio)
        self.assertIn(f"removed_embedded_art:{audio}", actions)

    def test_rejected_sidecar_no_leaves_embedded_art(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "Song.flac"
            audio.write_bytes(b"audio")
            sidecar = root / "Song.jpg"
            sidecar.write_bytes(b"image")
            actions = [f"exported_art:{sidecar}"]
            with mock.patch.object(
                audit, "artwork_review_choice", return_value=False
            ), mock.patch.object(
                audit, "recycle_path", side_effect=lambda path: Path(path)
            ), mock.patch.object(
                audit, "remove_embedded_artwork"
            ) as remove, contextlib.redirect_stdout(io.StringIO()):
                audit.review_extracted_art_sidecars(
                    actions,
                    use_color=False,
                    key_reader=lambda: "n",
                    audio_path=audio,
                )
        remove.assert_not_called()


if __name__ == "__main__":
    unittest.main()
