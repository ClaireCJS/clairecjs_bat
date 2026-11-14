import io
import unittest
from unittest import mock

import audit_music_batch as audit


class PagerProgressRedrawTests(unittest.TestCase):
    def test_carriage_return_refreshes_do_not_consume_page_rows(self):
        stream = io.StringIO()

        def unexpected_page_key():
            raise AssertionError("progress redraw incorrectly triggered pager")

        with mock.patch.object(
            audit,
            "visible_console_size",
            return_value=audit.os.terminal_size((40, 6)),
        ):
            pager = audit.ConsolePager(stream, key_reader=unexpected_page_key)
            try:
                text = "".join(
                    f"\r🎤 Baking: {percent:3d}%|████| {percent}/100"
                    for percent in range(101)
                )
                pager.write(text + "\nnext phase\n")
                pager.wait_for_output()
                self.assertEqual(pager.rows_used, 2)
                self.assertIn("100/100", stream.getvalue())
                self.assertIn("next phase", stream.getvalue())
            finally:
                pager.close()


if __name__ == "__main__":
    unittest.main()
