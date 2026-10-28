"""Regression for the Windows Terminal screenshot: 'all ❿of My ...'."""
import unittest
import play_audio_file as p


class CircledTenSpacingTests(unittest.TestCase):
    def styled(self, text, *, terminal=True, current=True, style=1):
        return p.stylize_karaoke_with_emojimax(
            text, style, True, 1.0, force_emoji_when_enabled=current,
            fade_threshold_percent=0, windows_terminal_compat=terminal)

    def test_spelled_numeric_and_plural_ten_get_terminal_safety_cells(self):
        for word in ('ten', '10', 'tens'):
            with self.subTest(word=word):
                self.assertEqual('❿   of', self.styled(word + ' of'))

    def test_screenshot_phrase_preserves_gap_through_wrap_and_color(self):
        for current in (True, False):
            text = self.styled('all ten of My fingers and toes', current=current)
            self.assertIn('❿   of', text)
            lines = p.wrap_to_cells(p.compensate_double_height_cells(text), 24)
            self.assertTrue(any('❿   of' in line for line in lines), lines)
            for line in lines:
                for treatment in range(1, len(p.KARAOKE_TREATMENT_NAMES) + 1):
                    painted = p.colorize_karaoke_text(line, treatment, 0, 1.0)
                    self.assertEqual(line, p.ANSI_CSI_RE.sub('', painted))

    def test_all_ten_negative_digits_share_sung_and_neighbor_geometry(self):
        for number, glyph in enumerate('❶❷❸❹❺❻❼❽❾❿', 1):
            for style in (1, 2, 5):
                with self.subTest(number=number, style=style):
                    sung = self.styled(f'{number} qzx', style=style)
                    neighbor = self.styled(f'{number} qzx', current=False, style=style)
                    self.assertEqual(sung, neighbor)
                    self.assertIn(glyph + '   ', sung)
                    self.assertEqual([sung], p.wrap_to_cells(sung, 80))

    def test_safety_cells_count_when_wrapping_at_exact_boundary(self):
        text = self.styled('ten of')
        width = p.terminal_cell_width(text)
        self.assertEqual([text], p.wrap_to_cells(text, width))
        self.assertEqual(['❿', 'of'], p.wrap_to_cells(text, width - 1))

    def test_other_surfaces_literal_numbers_and_compounds_keep_their_behavior(self):
        self.assertEqual('❿ of', self.styled('ten of', terminal=False))
        for terminal in (True, False):
            self.assertEqual('❿ of', self.styled('❿ of', terminal=terminal))
        self.assertEqual('❹⓿  ', p.windows_terminal_emojimax_replacement('❹⓿'))
        self.assertEqual('①⑤', p.windows_terminal_emojimax_replacement('①⑤'))


if __name__ == '__main__': unittest.main()
