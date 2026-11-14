import io
import sys
import unittest
from unittest import mock

import audit_music_batch as audit


class TtyBuffer(io.StringIO):
    def isatty(self):
        return True


class PagerStreamTests(unittest.TestCase):
    def test_interactive_stdout_and_stderr_share_one_writer(self):
        stdout = TtyBuffer()
        stderr = TtyBuffer()
        stdin = TtyBuffer()
        original = (sys.stdout, sys.stderr, sys.stdin)
        with (
            mock.patch.object(sys, "stdout", stdout),
            mock.patch.object(sys, "stderr", stderr),
            mock.patch.object(sys, "stdin", stdin),
        ):
            with audit.paged_console_output():
                self.assertIs(sys.stdout, sys.stderr)
                self.assertTrue(sys.stdout.isatty())
            self.assertIs(sys.stdout, stdout)
            self.assertIs(sys.stderr, stderr)
        self.assertIs(sys.stdin, original[2])


if __name__ == "__main__":
    unittest.main()
