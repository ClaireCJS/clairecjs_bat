import contextlib
import io
from pathlib import Path
from unittest import TestCase, mock

import audit_music_batch as audit


class ArtworkFolderTests(TestCase):
    def test_folder_approval_is_exact_folder_and_run_only(self):
        for key in ("f", "F"):
            memory = {}
            renderer = mock.Mock(return_value="test")
            def review(path, answer, state=memory):
                return audit.artwork_review_choice(
                    Path(path), label="art", use_color=False,
                    key_reader=answer, preview_renderer=renderer,
                    approval_memory=state,
                )
            with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(audit, "image_resolution", return_value="10x10"):
                self.assertTrue(review("album/first.jpg", lambda: key))
                never = mock.Mock(side_effect=AssertionError("must not prompt"))
                self.assertTrue(review("album/second.jpg", never))
                never.assert_not_called()
                self.assertEqual(renderer.call_count, 1)
                # Neither descendants, siblings, nor a fresh run inherit F.
                for path in ("album/disc2/art.jpg", "other/art.jpg"):
                    reader = mock.Mock(return_value="n")
                    self.assertFalse(review(path, reader))
                    reader.assert_called_once()
                self.assertFalse(review("album/first.jpg", lambda: "n", {}))
            self.assertFalse(memory.get("always", False))

    def test_legend_matches_available_controls(self):
        for colored in (False, True):
            self.assertIn("F=Keep for this folder", audit.artwork_review_choices(colored, allow_always=True))
            self.assertNotIn("F=", audit.artwork_review_choices(colored))
