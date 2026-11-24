from pathlib import Path
import contextlib
import io
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class FilenameModifierAndAlbumPromptTests(unittest.TestCase):
    def test_parenthesized_modifier_and_question_mark_boundary_are_preserved(self) -> None:
        unchanged = "3_Charlie Did Ya Know_ (acoustic).flac"
        self.assertIsNone(audit.capitalized_album_filename_proposal(unchanged, 7))
        proposal = audit.capitalized_album_filename_proposal(
            "3_charlie did ya know_ (acoustic).flac",
            7,
        )
        self.assertEqual("3_Charlie Did Ya Know_ (acoustic).flac", proposal)
        self.assertEqual(
            "Charlie Did Ya Know_ (acoustic)",
            audit.canonical_song_title_text("Charlie Did Ya Know_ (acoustic)"),
        )

    def test_shift_enter_skips_remaining_missing_albums_in_one_folder(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            findings = [
                {
                    "code": f"missing-album-{index}",
                    "category": "missing_album",
                    "path": f"{index}_Song.flac",
                    "severity": "review",
                    "message": "Missing album tag.",
                    "details": {},
                }
                for index in (1, 2)
            ]
            prompts: list[str] = []
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = audit.interactive_apply(
                    {"resolved_root": str(root), "findings": findings},
                    use_color=False,
                    input_reader=lambda prompt: prompts.append(prompt) or "\x1b[13;2u",
                )
        self.assertEqual(1, len(prompts))
        self.assertIn("Shift+ENTER=leave unchanged for rest of this folder", prompts[0])
        self.assertEqual("", result["applied_codes"])
        self.assertEqual("missing-album-1missing-album-2", result["skipped_codes"])
        self.assertIn("skipped for this folder", output.getvalue())

    def test_before_after_panels_each_receive_full_single_review_geometry(self) -> None:
        geometry = audit.ArtworkPreviewGeometry(200, 44, 0, 160, 35, 1600, 700)
        prepared = audit.PreparedArtworkPreview("direct Chafa 1.18.2 Sixel", geometry)
        with mock.patch.object(
            audit,
            "prepare_waveform_preview",
            return_value=prepared,
        ) as prepare, mock.patch.object(
            audit,
            "emit_prepared_artwork_preview",
            return_value="direct Chafa 1.18.2 Sixel",
        ) as emit, contextlib.redirect_stdout(io.StringIO()):
            mode = audit.render_waveform_before_after_panels(
                Path("before.jpg"),
                Path("after.jpg"),
                use_color=True,
            )
        self.assertEqual("direct Chafa 1.18.2 Sixel", mode)
        self.assertEqual(2, prepare.call_count)
        for call in prepare.call_args_list:
            self.assertEqual(audit.WAVEFORM_REVIEW_WIDTH_FRACTION, call.kwargs["width_fraction"])
            self.assertEqual(audit.WAVEFORM_REVIEW_HEIGHT_SCALE, call.kwargs["height_scale"])
        self.assertEqual(2, emit.call_count)


if __name__ == "__main__":
    unittest.main(verbosity=2)
