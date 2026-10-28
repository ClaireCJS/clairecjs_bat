"""Focused V577 HUD, Emojimaxx, and frequency-editor regressions."""
import unittest

import PAFPlayer as player


class V577HudFrequencyTests(unittest.TestCase):
    def test_removed_emoji_substitutions_stay_literal(self):
        for word in ("graveyard", "graveyards", "fried"):
            with self.subTest(word=word):
                self.assertNotIn(word, player.semantic)

    def test_album_value_aligns_with_visible_play_path_album(self):
        play = (
            "▶ Play: T:\\new\\MUSIC\\changerrecent\\Vial\\"
            r"2019 - Grow Up [original version]\6_Tension.flac (2m53s)"
        )
        tags = {
            "Artist": "Vial", "Song": "Tension", "Album": "Grow Up [original version]",
            "Year": "2019", "Genre": "Punk", "URL": "vialpunk.bandcamp.com",
        }
        expected = player.hud_play_album_anchor(play, tags["Album"])
        self.assertEqual(47, expected)
        for width in (140, 142, 144):
            with self.subTest(width=width):
                rows, _ = player.format_tag_panel(tags, width=width, play_header_text=play)
                album_row = next(row for row in rows if "Album: Grow Up" in row)
                actual = player.terminal_cell_width(album_row[:album_row.index("Grow Up")])
                self.assertEqual(expected, actual)
                self.assertLessEqual(player.terminal_cell_width(album_row), width)

    def test_frequency_editor_explains_axes_and_keeps_named_profiles(self):
        html = player._paf_web_html()
        for token in (
            "Custom Frequency Spread", "Left to right is display width",
            "bottom to top is source frequency", "frequencyWarpExplanation",
            "frequencyWarpProfileName", "frequencyWarpSaveProfile",
            "frequencyWarpLoadProfile", "frequencyWarpDeleteProfile",
            "Source frequency percentile at display ",
        ):
            self.assertIn(token, html)


if __name__ == "__main__":
    unittest.main()
