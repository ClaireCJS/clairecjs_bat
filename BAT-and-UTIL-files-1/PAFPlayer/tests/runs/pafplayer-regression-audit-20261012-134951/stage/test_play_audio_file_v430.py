"""Focused regressions for V430 curation and Windows console transport."""
import unittest
from unittest import mock

import play_audio_file as p


class _WindowsConsoleIO:
    """Name-compatible raw stream marker used by the console-write test."""


class FakeTextStream:
    def __init__(self, *, tty=True, partial=False):
        self.buffer = type("Buffer", (), {"raw": _WindowsConsoleIO()})()
        self.tty = tty
        self.partial = partial
        self.writes = []
        self.flushes = 0

    def isatty(self):
        return self.tty

    def write(self, value):
        amount = max(1, len(value) // 2) if self.partial and value else len(value)
        self.writes.append(value[:amount])
        return amount

    def flush(self):
        self.flushes += 1


class NoneReturningTextStream(FakeTextStream):
    def write(self, value):
        self.writes.append(value)
        return None


class PartialBinaryStream:
    def __init__(self, maximum=3):
        self.maximum = maximum
        self.payload = bytearray()
        self.write_calls = 0
        self.flushes = 0

    def write(self, value):
        raw = bytes(value)
        count = min(self.maximum, len(raw))
        self.payload.extend(raw[:count])
        self.write_calls += 1
        return count

    def flush(self):
        self.flushes += 1


class V430EmojimaxTests(unittest.TestCase):
    def test_final_cleanup_removes_requested_exact_word_mappings(self):
        for word in p.EMOJIMAX_V430_REMOVED:
            with self.subTest(word=word):
                self.assertIsNone(p.emojimax_replacement_for_key(word))
                self.assertNotIn(word, p.semantic)
                self.assertEqual(word, p.emojimax_plain_with_solutions(word)[0])

    def test_ladies_has_a_distinct_feminine_mapping(self):
        self.assertEqual("👩‍🤝‍👩", p.emojimax_replacement_for_key("ladies"))
        self.assertNotEqual(
            p.emojimax_replacement_for_key("ladies"),
            p.emojimax_replacement_for_key("men"),
        )


class V430ConsoleTransportTests(unittest.TestCase):
    def test_large_real_windows_console_text_is_bounded_and_flushed(self):
        stream = FakeTextStream()
        payload = "A" * 15000 + "▌" + "B" * 14999
        with mock.patch.object(p.sys, "stdout", stream):
            p.write_console(payload)
        self.assertGreater(len(stream.writes), 1)
        self.assertTrue(all(len(chunk) <= p.WINDOWS_CONSOLE_SAFE_WRITE_CHARS for chunk in stream.writes))
        self.assertEqual(payload, "".join(stream.writes))
        self.assertEqual(len(stream.writes), stream.flushes)

    def test_surrogate_pair_is_not_split_at_a_chunk_boundary(self):
        stream = FakeTextStream()
        payload = "A" * 4095 + "\ud83d\ude00" + "B" * 4095
        with mock.patch.object(p.sys, "stdout", stream):
            p.write_console(payload)
        self.assertEqual(payload, "".join(stream.writes))
        for chunk in stream.writes:
            self.assertFalse(chunk.endswith("\ud83d"))

    def test_redirected_output_keeps_the_short_write_fast_path(self):
        stream = FakeTextStream(tty=False)
        payload = "X" * 12000 + "▌"
        with mock.patch.object(p.sys, "stdout", stream):
            p.write_console(payload)
        self.assertEqual([payload], stream.writes)
        self.assertEqual(1, stream.flushes)

    def test_text_stream_partial_writes_are_completed(self):
        stream = FakeTextStream(partial=True)
        payload = "short Unicode ▌ payload"
        with mock.patch.object(p.sys, "stdout", stream):
            p.write_console(payload)
        self.assertEqual(payload, "".join(stream.writes))

    def test_console_adapter_returning_none_is_treated_as_a_completed_write(self):
        stream = NoneReturningTextStream()
        payload = "console adapter ▌ accepted this"
        with mock.patch.object(p.sys, "stdout", stream):
            p.write_console(payload)
        self.assertEqual([payload], stream.writes)
        self.assertEqual(1, stream.flushes)

    def test_binary_terminal_payloads_are_not_decoded_and_partial_writes_continue(self):
        binary = PartialBinaryStream()
        stream = FakeTextStream()
        stream.buffer = binary
        payload = b"\x1bPq\xff\x80\x00\x9c\x1b\\"
        with mock.patch.object(p.sys, "stdout", stream):
            p.write_console_bytes(payload)
        self.assertEqual(payload, bytes(binary.payload))
        self.assertGreater(binary.write_calls, 1)


if __name__ == "__main__":
    unittest.main()
