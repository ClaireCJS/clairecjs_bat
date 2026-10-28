"""Regression coverage for the hot Emojimaxx glyph beside punctuation."""

import unittest

import PAFPlayer as app


class HotEmojiSpacingTests(unittest.TestCase):
    def test_hot_uses_emoji_presentation_and_two_console_cells(self):
        self.assertEqual("♨️", app.semantic["hot"])
        self.assertEqual(2, app.terminal_cell_width(app.semantic["hot"]))

    def test_console_keeps_source_space_before_ampersand(self):
        source = "Too hot & too fast"
        for windows_terminal_compat in (False, True):
            with self.subTest(windows_terminal_compat=windows_terminal_compat):
                rendered = app.stylize_karaoke_with_emojimax(
                    source, 1, True, force_emoji_when_enabled=True,
                    windows_terminal_compat=windows_terminal_compat,
                )
                self.assertEqual("Too ♨️ & too fast", rendered)
                self.assertEqual(
                    app.terminal_cell_width("Too ♨️ & too fast"),
                    app.terminal_cell_width(rendered),
                )

    def test_plain_and_phrase_paths_keep_the_same_glyph(self):
        plain, solutions = app.emojimax_plain_with_solutions("hot & hot dog")
        self.assertEqual("♨️ & 🌭", plain)
        self.assertEqual(
            [("♨️", "hot"), ("🌭", "hot dog")],
            [(item["display"], item["solution"]) for item in solutions],
        )

    def test_rainbow_and_hash_colors_do_not_split_emoji_selector(self):
        lyric = "Too ♨️ & too fast"
        self.assertIn("♨️", app.karaoke_display_clusters(lyric))
        for treatment in (2, 4):
            with self.subTest(treatment=treatment):
                colored = app.colorize_karaoke_text(lyric, treatment)
                self.assertIn("♨️", colored)
                self.assertEqual(lyric, app.ANSI_CSI_RE.sub("", colored))


if __name__ == "__main__":
    unittest.main()
