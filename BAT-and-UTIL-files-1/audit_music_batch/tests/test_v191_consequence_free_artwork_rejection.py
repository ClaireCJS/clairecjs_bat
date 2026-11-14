from pathlib import Path
import contextlib
import io
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class V191ConsequenceFreeArtworkRejectionTests(unittest.TestCase):
    def test_rejecting_new_art_recycles_after_guarded_rename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "Song.flac"
            audio.write_bytes(b"audio")
            # Force the rejected name to use the collision-preserving (1)
            # spelling from the user's real failure.
            (root / "Song.rejected-by-username.jpg").write_bytes(b"older")
            guard = audit.ActionChangeGuard(root)
            sidecar = root / "Song.jpg"
            recycle_bin = root / "recycle"
            recycle_bin.mkdir()

            def fake_send2trash(value: str) -> None:
                source = Path(value)
                source.rename(recycle_bin / source.name)

            actions = []
            output = io.StringIO()
            with mock.patch.object(audit, "_ACTIVE_CHANGE_GUARD", guard), \
                 mock.patch.object(audit, "send2trash", fake_send2trash), \
                 mock.patch.object(
                     audit, "artwork_review_choice", return_value=False
                 ), contextlib.redirect_stdout(output):
                audit.check_pending_change(sidecar)
                sidecar.write_bytes(b"newly extracted")
                actions.append(f"exported_art:{sidecar}")
                approved = audit.review_extracted_art_sidecars(
                    actions,
                    use_color=False,
                    key_reader=lambda: "n",
                    audio_path=audio,
                )

            self.assertFalse(approved)
            self.assertFalse(sidecar.exists())
            self.assertTrue(
                (recycle_bin / "Song.rejected-by-username (1).jpg").is_file()
            )
            self.assertNotIn("Refresh the proposal", output.getvalue())

    def test_stale_change_messages_are_plain_user_language(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = root / "item.txt"
            item.write_text("old", encoding="utf-8")
            guard = audit.ActionChangeGuard(root)
            item.write_text("new and externally changed", encoding="utf-8")
            with self.assertRaises(audit.ExternalFileChange) as raised:
                guard.check(item)
            message = str(raised.exception)
            self.assertIn("Nothing was changed", message)
            self.assertNotIn("proposal", message.casefold())


if __name__ == "__main__":
    unittest.main()
