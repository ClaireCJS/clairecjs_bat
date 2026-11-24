import tempfile
import unittest
from pathlib import Path
from unittest import mock

import audit_music_batch as audit


class TrackArtExportTests(unittest.TestCase):
    def test_identical_image_under_other_name_does_not_suppress_export(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            audio = folder / "My Track.flac"
            audio.write_bytes(b"audio placeholder")
            (folder / "Someone Else.jpg").write_bytes(b"\xff\xd8\xffcover")
            with mock.patch.object(
                audit, "embedded_pictures",
                return_value=[(b"\xff\xd8\xffcover", "image/jpeg", 3, "")],
            ):
                exports = audit.export_art_sidecars(audio)
            self.assertEqual([str(folder / "My Track.jpg")], exports)
            self.assertEqual(b"\xff\xd8\xffcover", (folder / "My Track.jpg").read_bytes())

    def test_exact_same_sidecar_is_reused_without_numbered_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            audio = folder / "My Track.flac"
            (folder / "My Track.jpg").write_bytes(b"same")
            with mock.patch.object(
                audit, "embedded_pictures",
                return_value=[(b"same", "image/jpeg", 3, "")],
            ):
                self.assertEqual([], audit.export_art_sidecars(audio))
            self.assertFalse((folder / "My Track (1).jpg").exists())

    def test_different_existing_sidecar_is_a_conflict_not_numbered_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            audio = folder / "My Track.flac"
            (folder / "My Track.jpg").write_bytes(b"different")
            with mock.patch.object(
                audit, "embedded_pictures",
                return_value=[(b"embedded", "image/jpeg", 3, "")],
            ):
                with self.assertRaises(FileExistsError):
                    audit.export_art_sidecars(audio)
            self.assertFalse((folder / "My Track (1).jpg").exists())


if __name__ == "__main__":
    unittest.main()
