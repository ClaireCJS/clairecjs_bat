#!/usr/bin/env python3

"""Return subtitle length in seconds for SRT and LRC files."""

from __future__ import annotations

import argparse
import codecs
import locale
import re
import sys
from pathlib import Path


RETURN_CODES = {
    -1: "no usable timestamp / length could be retrieved",
    -2: "unsupported or wrong file extension",
    -3: "file could not be read",
    -4: "file bytes could not be decoded with any fallback encoding",
}

SUPPORTED_EXTENSIONS = {".srt", ".lrc"}
ERROR_STYLE = "\033[1;37;41m"
RESET_STYLE = "\033[0m"
BANG = "\U0001f4a5"

SRT_RANGE_RE = re.compile(
    r"(?P<start>\d{1,3}:\d{2}:\d{2}(?:[,.]\d{1,3})?)\s*-->\s*"
    r"(?P<end>\d{1,3}:\d{2}:\d{2}(?:[,.]\d{1,3})?)"
)
SRT_ANY_RE = re.compile(r"\b(?P<time>\d{1,3}:\d{2}:\d{2}(?:[,.]\d{1,3})?)\b")
LRC_RE     = re.compile(r"\[\s*(?P<time>\d{1,3}(?::\d{1,2})?(?:[.:]\d{1,3})?)\s*\]")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass


def stderr_error(message: str) -> None:
    print(f"{ERROR_STYLE}{BANG} {message} {BANG}{RESET_STYLE}", file=sys.stderr)


def effective_extension(path: Path) -> str:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes and suffixes[-1] == ".maybe":
        suffixes.pop()
    return suffixes[-1] if suffixes else ""


def encoding_candidates(data: bytes) -> list[str]:
    preferred = locale.getpreferredencoding(False)
    candidates = [
        "utf-8-sig",
        "utf-8",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "utf-32",
        "utf-32-le",
        "utf-32-be",
        preferred,
        "cp1252",
        "latin-1",
        "cp1250",
        "cp1251",
        "cp1253",
        "cp1254",
        "cp1255",
        "cp1256",
        "cp1257",
        "cp1258",
        "iso-8859-1",
        "iso-8859-2",
        "iso-8859-5",
        "iso-8859-6",
        "iso-8859-7",
        "iso-8859-8",
        "iso-8859-9",
        "iso-8859-15",
        "gb18030",
        "gbk",
        "big5",
        "shift_jis",
        "cp932",
        "euc_jp",
        "iso2022_jp",
        "euc_kr",
        "cp949",
        "koi8_r",
        "koi8_u",
        "mac_roman",
    ]

    if data.startswith(codecs.BOM_UTF8):
        candidates.insert(0, "utf-8-sig")
    elif data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        candidates.insert(0, "utf-16")
    elif data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        candidates.insert(0, "utf-32")

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.lower().replace("_", "-")
        if key not in seen:
            seen.add(key)
            deduped.append(candidate)
    return deduped


def decoded_score(text: str) -> int:
    sample = text[:65536]
    if not sample:
        return -1_000_000

    score = 0
    score += len(SRT_RANGE_RE.findall(sample)) * 5000
    score += len(      LRC_RE.findall(sample)) * 3000
    score += len(  SRT_ANY_RE.findall(sample)) * 500

    controls = sum(
        1
        for char in sample
        if (ord(char) < 32 and char not in "\r\n\t") or char == "\ufffd"
    )
    nulls     = sample.count("\x00")
    printable = sum(1 for char in sample if char.isprintable() or char in "\r\n\t")
    score    += int((printable / max(len(sample), 1)) * 1000)
    score    -= controls * 50
    score    -= nulls * 200
    return score


def decode_bytes(data: bytes) -> tuple[str | None, str | None]:
    if not data:
        return "", "empty"

    sample = data[: min(len(data), 65536)]
    scored: list[tuple[int, str]] = []

    for encoding in encoding_candidates(data):
        try:
            decoded_sample = sample.decode(encoding, errors="strict")
            scored.append((decoded_score(decoded_sample), encoding))
        except (LookupError, UnicodeError):
            continue

    for _score, encoding in sorted(scored, reverse=True):
        try:
            return data.decode(encoding, errors="strict"), encoding
        except UnicodeError:
            continue

    for encoding in ("utf-8-sig", "utf-16", "gb18030", "cp1252", "latin-1"):
        try:
            return data.decode(encoding, errors="replace"), f"{encoding} with replacement"
        except (LookupError, UnicodeError):
            continue

    return None, None


def srt_time_to_seconds(timestamp: str) -> float | None:
    match = re.fullmatch(r"(\d{1,3}):(\d{2}):(\d{2})(?:[,.](\d{1,3}))?", timestamp)
    if not match:
        return None
    hours, minutes, seconds, millis = match.groups()
    millis = (millis or "0").ljust(3, "0")[:3]
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def lrc_time_to_seconds(timestamp: str) -> float | None:
    timestamp = timestamp.strip()
    if ":" in timestamp:
        match = re.fullmatch(r"(\d{1,3}):(\d{1,2})(?:[.:](\d{1,3}))?", timestamp)
        if not match:
            return None
        minutes, seconds, fraction = match.groups()
        whole_seconds = int(minutes) * 60 + int(seconds)
    else:
        match = re.fullmatch(r"(\d{1,3})(?:[.](\d{1,3}))?", timestamp)
        if not match:
            return None
        seconds, fraction = match.groups()
        whole_seconds = int(seconds)

    frac_seconds = 0.0
    if fraction:
        frac_seconds = int(fraction.ljust(3, "0")[:3]) / 1000
    return whole_seconds + frac_seconds


def format_seconds(seconds: float) -> str:
    if seconds.is_integer():
        return str(int(seconds))
    return f"{seconds:.3f}".rstrip("0").rstrip(".")


def length_for_srt(text: str) -> float | None:
    ends = [
        parsed
        for parsed in (srt_time_to_seconds(match.group("end")) for match in SRT_RANGE_RE.finditer(text))
        if parsed is not None
    ]
    if ends:
        return max(ends)

    all_times = [
        parsed
        for parsed in (srt_time_to_seconds(match.group("time")) for match in SRT_ANY_RE.finditer(text))
        if parsed is not None
    ]
    return max(all_times) if all_times else None


def length_for_lrc(text: str) -> float | None:
    times = [
        parsed
        for parsed in (lrc_time_to_seconds(match.group("time")) for match in LRC_RE.finditer(text))
        if parsed is not None
    ]
    return max(times) if times else None


def process_file(filename: str) -> int | float:
    path = Path(filename)
    extension = effective_extension(path)
    if extension not in SUPPORTED_EXTENSIONS:
        stderr_error(
            f"Unsupported extension for {filename!r}: expected .srt, .lrc, .srt.maybe, or .lrc.maybe"
        )
        return -2

    try:
        data = path.read_bytes()
    except OSError as exc:
        stderr_error(f"Could not read {filename!r}: {exc}")
        return -3

    text, encoding = decode_bytes(data)
    if text is None:
        stderr_error(f"Could not decode {filename!r} with the available encoding fallbacks")
        return -4

    length = length_for_srt(text) if extension == ".srt" else length_for_lrc(text)
    if length is None:
        stderr_error(f"No subtitle timestamp length could be retrieved from {filename!r} ({encoding})")
        return -1
    return length


def build_parser() -> argparse.ArgumentParser:
    description = "Return subtitle length in seconds for SRT and LRC files."
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Return values printed to STDOUT:
  >= 0  length in seconds
  -1    no usable timestamp / length could be retrieved
  -2    unsupported or wrong file extension
  -3    file could not be read
  -4    file bytes could not be decoded with any fallback encoding

Extension handling:
  .srt and .lrc are supported.
  .srt.maybe and .lrc.maybe are treated as .srt and .lrc.

Examples:
  python subtitle_length.py captions.srt
  python subtitle_length.py synced.lyrics.lrc.maybe
  python subtitle_length.py one.srt two.lrc
  python subtitle_length.py --self-test
""",
    )
    parser.add_argument("--self-test", action="store_true", help="run built-in unit tests and exit")
    parser.add_argument("files", nargs="*", help="SRT or LRC files to inspect")
    return parser


def run_self_tests() -> int:
    import contextlib
    import io
    import tempfile
    import unittest

    class SubtitleLengthTests(unittest.TestCase):
        def test_lrc_accepts_common_and_weird_timestamp_variants(self):
            cases = {
                "10": 10.0,
                "10.0": 10.0,
                "00:10.0": 10.0,
                "0:10.0": 10.0,
                "0:10": 10.0,
                "03:04": 184.0,
                "03:04.56": 184.56,
            }

            for timestamp, expected in cases.items():
                with self.subTest(timestamp=timestamp):
                    self.assertEqual(lrc_time_to_seconds(timestamp), expected)

        def test_lrc_length_returns_final_timestamp(self):
            text = "[10]start\n[00:10.0]same\n[03:04.56]end\n"
            self.assertEqual(length_for_lrc(text), 184.56)

        def test_srt_accepts_integer_and_fractional_end_timestamps(self):
            integer_text = "1\n00:00:10 --> 00:00:12\nHi\n"
            fractional_text = "1\n00:00:10,000 --> 00:00:12,500\nHi\n"

            self.assertEqual(length_for_srt(integer_text), 12.0)
            self.assertEqual(length_for_srt(fractional_text), 12.5)

        def test_maybe_extension_uses_previous_extension(self):
            self.assertEqual(effective_extension(Path("song.lrc.maybe")), ".lrc")
            self.assertEqual(effective_extension(Path("captions.srt.maybe")), ".srt")

        def test_process_file_decodes_utf16_lrc(self):
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "song.lrc"
                path.write_bytes("[00:01]one\n[00:02.5]two\n".encode("utf-16"))

                self.assertEqual(process_file(str(path)), 2.5)

        def test_process_file_rejects_wrong_extension_and_writes_stderr(self):
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "not-subtitles.txt"
                path.write_text("[00:01]one\n", encoding="utf-8")
                stderr = io.StringIO()

                with contextlib.redirect_stderr(stderr):
                    result = process_file(str(path))

                self.assertEqual(result, -2)
                self.assertIn("Unsupported extension", stderr.getvalue())

        def test_process_file_returns_minus_one_when_no_timestamp_exists(self):
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "emptyish.srt"
                path.write_text("No timestamps here\n", encoding="utf-8")
                stderr = io.StringIO()

                with contextlib.redirect_stderr(stderr):
                    result = process_file(str(path))

                self.assertEqual(result, -1)
                self.assertIn("No subtitle timestamp", stderr.getvalue())

        def test_no_args_prints_usage_and_returns_success(self):
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = main([])

            self.assertEqual(result, 0)
            self.assertIn("usage:", stdout.getvalue())
            self.assertIn("-1    no usable timestamp", stdout.getvalue())

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SubtitleLengthTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_tests()

    if not args.files:
        parser.print_help(sys.stdout)
        return 0

    multiple = len(args.files) > 1
    had_error_code = False
    for filename in args.files:
        result = process_file(filename)
        had_error_code = had_error_code or (isinstance(result, int) and result < 0)
        value = str(result) if isinstance(result, int) else format_seconds(result)
        if multiple:
            print(f"{filename}\t{value}")
        else:
            print(value)

    return 1 if had_error_code else 0


if __name__ == "__main__":
    raise SystemExit(main())
