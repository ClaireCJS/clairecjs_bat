import io
import threading
import unittest
from unittest import mock

import audit_music_batch as audit


class ConsolePagerTests(unittest.TestCase):
    def test_output_buffers_while_more_prompt_waits_and_drains_before_input(self):
        stream = io.StringIO()
        pager_paused = threading.Event()
        release_pager = threading.Event()
        pause_calls = 0

        def read_pager_key():
            nonlocal pause_calls
            pause_calls += 1
            if pause_calls == 1:
                pager_paused.set()
                if not release_pager.wait(2):
                    raise AssertionError("test did not release pager key wait")
            return " "

        terminal = audit.os.terminal_size((2_000_000, 6))
        with mock.patch.object(audit, "visible_console_size", return_value=terminal):
            pager = audit.ConsolePager(stream, key_reader=read_pager_key)
            large_write_done = threading.Event()
            large_payload = "x" * 1_000_001

            def write_large_payload():
                pager.write(large_payload)
                large_write_done.set()

            try:
                self.assertEqual(pager.write("one\ntwo\nthree\nfour\n"), 19)
                self.assertTrue(pager_paused.wait(1), "pager never reached its key wait")

                # This is the important regression: ordinary writes from the
                # audit thread return even while the pager is awaiting a key.
                self.assertEqual(pager.write("buffered while paused\n"), 22)
                self.assertNotIn("buffered while paused", stream.getvalue())
                large_writer = threading.Thread(target=write_large_payload)
                large_writer.start()
                self.assertTrue(
                    large_write_done.wait(1),
                    "pager back-pressured output larger than one megabyte",
                )

                prompt_ready = threading.Event()

                def wait_at_next_prompt():
                    pager.wait_for_output()
                    prompt_ready.set()

                prompt_waiter = threading.Thread(target=wait_at_next_prompt)
                prompt_waiter.start()
                self.assertFalse(prompt_ready.wait(0.05))
                release_pager.set()
                self.assertTrue(prompt_ready.wait(1), "queued output did not drain")
                prompt_waiter.join(1)
                self.assertFalse(prompt_waiter.is_alive())
                rendered = stream.getvalue()
                self.assertLess(
                    rendered.index("four"),
                    rendered.index("buffered while paused"),
                )
                self.assertTrue(rendered.endswith(large_payload))
            finally:
                release_pager.set()
                pager.close()
                if "large_writer" in locals():
                    large_writer.join(1)


if __name__ == "__main__":
    unittest.main()
