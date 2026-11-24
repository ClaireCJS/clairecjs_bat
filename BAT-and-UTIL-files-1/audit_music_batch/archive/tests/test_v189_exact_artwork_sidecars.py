from pathlib import Path
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class V189ExactArtworkSidecarTests(unittest.TestCase):
    def test_numbered_track_recognizes_exact_same_basename_art(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "01_Compilation Song.flac"
            audio.write_bytes(b"audio")
            exact = root / "01_Compilation Song.jpg"
            exact.write_bytes(b"art")
            self.assertEqual(
                [exact],
                audit.same_basename_front_art_candidates(audio),
            )
            self.assertIn(
                exact,
                audit.BatchAudit(root).artwork_sidecars_for_audio(audio),
            )

    def test_track_sidecar_choice_uses_exact_name_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "01_Compilation Song.flac"
            audio.write_bytes(b"audio")
            extracted = root / "cover.jpg"
            extracted.write_bytes(b"art")
            actions = [f"exported_art:{extracted}"]
            with mock.patch.object(
                audit, "artwork_review_choice", return_value="sidecar"
            ):
                approved = audit.review_extracted_art_sidecars(
                    actions,
                    use_color=False,
                    audio_path=audio,
                )
            exact = root / "01_Compilation Song.jpg"
            self.assertTrue(approved)
            self.assertTrue(exact.is_file())
            self.assertFalse(extracted.exists())
            self.assertEqual([], list(root.glob("* (1).jpg")))

    def test_existing_exact_sidecar_never_creates_numbered_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "01_Compilation Song.flac"
            audio.write_bytes(b"audio")
            exact = root / "01_Compilation Song.jpg"
            exact.write_bytes(b"existing")
            extracted = root / "cover.jpg"
            extracted.write_bytes(b"new")
            actions = [f"exported_art:{extracted}"]
            with mock.patch.object(
                audit, "artwork_review_choice", return_value="sidecar"
            ):
                approved = audit.review_extracted_art_sidecars(
                    actions,
                    use_color=False,
                    audio_path=audio,
                )
            self.assertTrue(approved)
            self.assertEqual(b"existing", exact.read_bytes())
            self.assertEqual([], list(root.glob("* (1).jpg")))
            self.assertTrue(
                any(action == f"already_present_track_art:{exact}" for action in actions)
            )


if __name__ == "__main__":
    unittest.main()
