from pathlib import Path
import contextlib
import io
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class PersistentMissingAlbumSkipTests(unittest.TestCase):
    def test_ctrl_shift_enter_is_distinct_from_shift_enter(self) -> None:
        self.assertEqual(
            ("\x1b[13;6u", True, True),
            audit.read_album_tag_value("Album: ", input_reader=lambda _: "\x1b[13;6u"),
        )
        self.assertEqual(
            ("\x1b[13;2u", True, False),
            audit.read_album_tag_value("Album: ", input_reader=lambda _: "\x1b[13;2u"),
        )

    def test_ctrl_shift_enter_skips_this_folder_in_future_audits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "music"
            root.mkdir()
            database = Path(directory) / "remembered.sqlite3"

            def finding(index: int) -> dict:
                return {
                    "code": f"missing-album-{index}",
                    "category": "missing_album",
                    "path": f"{index}_Song.flac",
                    "severity": "review",
                    "message": "Missing album tag.",
                    "details": {},
                }

            prompts = []
            with mock.patch.object(audit, "remembered_no_database_path", return_value=database):
                with contextlib.redirect_stdout(io.StringIO()):
                    audit.interactive_apply(
                        {"resolved_root": str(root), "findings": [finding(1), finding(2)]},
                        use_color=False,
                        input_reader=lambda prompt: prompts.append(prompt) or "\x1b[13;6u",
                    )
                self.assertEqual(1, len(prompts))
                self.assertIn("Ctrl+Shift+ENTER", prompts[0])
                self.assertEqual(
                    "skip_album",
                    audit.RememberedNoStore(database).folder_choice("missing_album", root),
                )
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    audit.interactive_apply(
                        {"resolved_root": str(root), "findings": [finding(3)]},
                        use_color=False,
                        input_reader=lambda prompt: self.fail("album prompt should be remembered"),
                    )
                self.assertIn("remembered Ctrl+Shift+ENTER", output.getvalue())


if __name__ == "__main__":
    unittest.main()
