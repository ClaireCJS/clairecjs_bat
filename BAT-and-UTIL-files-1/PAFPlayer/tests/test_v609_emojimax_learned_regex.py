"""V609 Emojimaxx curation and saved learned-selector regressions."""

from datetime import datetime
from pathlib import Path
import unittest
from unittest import mock

import PAFPlayer as app


RUN = Path(__file__).resolve().parent / "runs" / (
    "v609-emojimax-learned-" + datetime.now().strftime("%Y%m%d%H%M%S%f"))


class EmojimaxAndLearnedRegexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RUN.mkdir(parents=True, exist_ok=False)

    def test_product_remains_literal_and_whip_mapping_is_preserved(self):
        self.assertNotIn("product", app.semantic)
        self.assertNotIn("product", app.SEMANTIC_PHRASES)
        for word in ("product", "Product", "PRODUCT", "products"):
            with self.subTest(word=word):
                self.assertIsNone(app.emojimax_replacement_for_key(word))
                self.assertEqual((word, []), app.emojimax_plain_with_solutions(word))
        self.assertEqual("𓀓𓀝", app.emojimax_replacement_for_key("whip"))

    def test_track_number_selectors_end_at_a_real_separator(self):
        cases = {
            "05_Sellout.flac": r"^05[ _-]",
            "05 Sellout.flac": r"^05[ _-]",
            "05-Sellout.flac": r"^05[ _-]",
            "4_01_North Pappy.flac": r"^4[ _-]01[ _-]",
            "4-01 North Pappy.flac": r"^4[ _-]01[ _-]",
        }
        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                selector = app._attrib_rule_selector_for_audio(RUN / filename)
                self.assertEqual(expected, selector)
                self.assertFalse(selector.endswith(".*"))

    def test_written_rule_has_no_trailing_wildcard_and_stays_track_specific(self):
        album = RUN / "album"
        album.mkdir()
        wanted = album / "4_01_North Pappy.flac"
        sibling = album / "4_02_The Mollusk.flac"
        longer_number = album / "4_010_Other.flac"
        for path in (wanted, sibling, longer_number):
            path.write_bytes(b"fixture")
        target, rule, attributes = app.append_marked_attribute_rule(wanted, "learned")
        selector = rule.split(":", 1)[0]
        self.assertEqual(r"^4[ _-]01[ _-]:learned", rule)
        self.assertEqual(("learned",), attributes)
        self.assertFalse(selector.endswith(".*"))
        self.assertEqual(1, app._attrib_selector_match_count(selector, wanted))
        self.assertIn(rule, target.read_text(encoding="utf-8"))

    def test_writer_rejects_a_future_trailing_wildcard_before_creating_file(self):
        album = RUN / "guard"
        album.mkdir()
        song = album / "05_Sellout.flac"
        song.write_bytes(b"fixture")
        with mock.patch.object(app, "_attrib_rule_selector_for_audio", return_value="^05.*"):
            with self.assertRaisesRegex(ValueError, "must not end"):
                app.append_marked_attribute_rule(song, "learned")
        self.assertFalse((album / "attrib.lst").exists())


if __name__ == "__main__":
    unittest.main()
