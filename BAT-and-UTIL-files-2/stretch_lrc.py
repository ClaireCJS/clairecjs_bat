#!/usr/bin/env python3
"""
Slide or remap LRC timestamps.

This is for stretching LRCs made from studio versions of songs so they are
suitable for live versions of the song, which may be played faster or
slower and offset by singer banter/crowd noise, and therefore need
a completely different set of timestamps that are proportional to the original.

Accepts +/- and floating point number of seconds to offset every timestamp as
an alternate call.

Primary call is to accept 2 timestamps: the new first-lyric-sung and last-lyric-sung
timestamples, i.e.:

        stretch_lrc song.mp3 0:30,4:56

Maybe song.mp3 initially started at 0:10 and ended at 5:25, but the live version starts
with 20 seconds of crowd banter, and is played more slowly so it finishes later.

This would produce an LRC where the lyric timing would actually match!

"""

from __future__ import annotations

import ctypes
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path
from typing import Callable


getcontext().prec = 40

EXIT_OK = 0
EXIT_ERROR = 1
DEFAULT_ADDED_FRACTION_DIGITS = 2
MAX_TIMESTAMP_TOKEN_CHARS = 64
RESET_COLOR = "\033[0m"

BRACKETED_TEXT_RE  = re.compile(r"([\[<])([^\[\]<>\r\n]{0,64})([\]>])")
BRACKETED_BYTES_RE = re.compile(rb"([\[<])([^\[\]<>\r\n]{0,64})([\]>])")
SECONDS_DELTA_RE   = re.compile(
    r"^\s*([+-]?(?:\d+(?:[\.,]\d*)?|[\.,]\d+))(?:\s*(?:s|sec|secs|second|seconds))?\s*$",
    re.IGNORECASE,
)


ESC           =  "\x1b"                           # the escape character
RESET         = f"{ESC}[0m"                       # reset color back to default
BRIGHT_CYAN   = f"{ESC}[96m"                      # column 1 (Du)
GREEN         = f"{ESC}[32m"                      # success
BRIGHT_GREEN  = f"{ESC}[42m"                      # success
CYAN          = f"{ESC}[36m"                      # column 2 (Overlap)
RED           = f"{ESC}[31m"                      # column 3 (Lines)
FAINT_ON      = f"{ESC}[2m"
FAINT_OFF     = f"{ESC}[22m"
ITALICS_ON    = f"{ESC}[3m"
ITALICS_OFF   = f"{ESC}[23m"
UNDERLINE_ON  = f"{ESC}[4m"
UNDERLINE_OFF = f"{ESC}[24m"
BRIGHT_RED    = f"{ESC}[91m"                      # errors
BRIGHT_YELLOW = f"{ESC}[93m"                      # warnings
ORANGE        = f"{ESC}[38;2;235;107;0m"          # column 4 (Lyrics)
MAGENTA       = f"{ESC}[35m"                      # borders/lines
BRIGHT_GREEN  = f"{ESC}[92m"                      # header text
BIG_TOP       = f"{ESC}#3"                        # double-height text: on. Font/Mode =  top   half of double-height text
BIG_BOT       = f"{ESC}#4"                        # double-height text: on. Font/Mode = bottom half of double-height text
BIG_OFF       = f"{ESC}#5"                        # double-height text: off




@dataclass(frozen=True)
class TimestampStyle:
    kind: str
    minute_width: int = 1
    second_width: int = 2
    fraction_width: int = 0
    fraction_separator: str = "."
    time_separator: str = ":"
    leading_colon: bool = False
    hour_width: int = 0
    had_fraction: bool = False
    leading_space: str = ""
    trailing_space: str = ""


@dataclass(frozen=True)
class ParsedTimestamp:
    seconds: Decimal
    style: TimestampStyle


@dataclass(frozen=True)
class TransformPlan:
    transform_seconds: Callable[[Decimal], Decimal]
    mode: str
    original_start: Decimal
    original_final: Decimal
    new_start: Decimal | None
    new_final: Decimal
    final_delta: Decimal
    duration_delta: Decimal | None
    backup_label: str


def enable_ansi() -> None:
    """Enable ANSI escape processing on Windows terminals when possible."""
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        for stream in (-11, -12):  # STD_OUTPUT_HANDLE, STD_ERROR_HANDLE
            handle = kernel32.GetStdHandle(stream)
            if handle in (0, -1):
                continue
            mode = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                continue
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def env_color(name: str, default: str) -> str:
    value = os.environ.get(name, default)
    return (
        value.replace("\\e", "\033")
        .replace("\\E", "\033")
        .replace("\\x1b", "\033")
        .replace("\\033", "\033")
        .replace("^[", "\033")
    )


enable_ansi()
ERROR_COLOR = env_color("ansi_color_error", "\033[91m")
WARNING_COLOR = env_color("ansi_color_warning", "\033[93m")


def colorize(color: str, message: str) -> str:
    return f"{color}{message}{RESET_COLOR}" if color else message


def error(message: str) -> None:
    print(colorize(ERROR_COLOR, f"ERROR: {message}"), file=sys.stderr)


def warning(message: str) -> None:
    print(colorize(WARNING_COLOR, f"WARNING: {message}"), file=sys.stderr)


def usage() -> str:
    program = Path(sys.argv[0]).name
    return f"""Usage:
  {program} filename.lrc +2.45
  {program} filename.lrc -2.5s
  {program} filename.lrc 1:59
  {program} filename.lrc 0:35.22
  {program} filename.lrc 0:30,4:45

Slide or remap LRC timestamps.

This is for stretching LRCs made from studio versions of songs so they are
suitable for use as LRCs for live versions of the song, which are played
slightly faster or slower and thus have slightly different timestamps.

Parameter 1:
  The LRC filename. If it does not exist, this exits gracefully.

Parameter 2, usage 1:
  Number of seconds to slide every timestamp by. Use a positive or negative
  number, such as +2.45, -1, or -2.5s.

Parameter 2, usage 2:
  New final timestamp, such as 1:59 or 0:35.22. If this argument contains a
  colon, the script compares it to the original final timestamp, calculates the
  slide in seconds, then moves every timestamp by that amount.

Parameter 2, usage 3:
  New beginning and final timestamps, separated by a comma, such as 0:30,4:45.
  This maps the original earliest timestamp to the new beginning, and the
  original final timestamp to the new ending. Use this when a live song needs
  both a slide and a stretch.

Recognized timestamp examples:
  [30]  [:30]  [0:30]  [00:30.25]  [0.30.00]  [00:30:25]

Before replacing the file, the original is backed up as:
  whatever.before_+2.45_second_slide.YYYYMMDDHHMMSS.bak
  whatever.before_+10_second_slide_+5_second_stretch.YYYYMMDDHHMMSS.bak
"""


def parse_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def split_seconds_and_fraction(value: str) -> tuple[str, str, str] | None:
    separators = [pos for pos, char in enumerate(value) if char in ".,:"]
    decimal_separators = [pos for pos in separators if value[pos] in ".,"]
    if len(decimal_separators) > 1:
        return None
    if len(decimal_separators) == 1:
        pos = decimal_separators[0]
        seconds_part = value[:pos]
        fraction_part = value[pos + 1 :]
        if not seconds_part.isdigit() or not fraction_part.isdigit():
            return None
        return seconds_part, value[pos], fraction_part
    if not value.isdigit():
        return None
    return value, "", ""


def fraction_to_decimal(fraction: str) -> Decimal:
    if not fraction:
        return Decimal(0)
    return Decimal(fraction) / (Decimal(10) ** len(fraction))


def parse_colon_timestamp(core: str, leading_space: str, trailing_space: str) -> ParsedTimestamp | None:
    parts = core.split(":")
    if len(parts) == 2:
        minutes_text, seconds_text = parts
        leading_colon = minutes_text == ""
        if leading_colon:
            minutes = Decimal(0)
            minute_width = 0
        elif minutes_text.isdigit():
            minutes = Decimal(int(minutes_text))
            minute_width = len(minutes_text)
        else:
            return None

        parsed_seconds = split_seconds_and_fraction(seconds_text)
        if parsed_seconds is None:
            return None
        whole_seconds_text, fraction_separator, fraction_text = parsed_seconds
        whole_seconds = int(whole_seconds_text)
        if whole_seconds >= 60:
            return None

        seconds = minutes * 60 + Decimal(whole_seconds) + fraction_to_decimal(fraction_text)
        style = TimestampStyle(
            kind="colon",
            minute_width=minute_width,
            second_width=len(whole_seconds_text),
            fraction_width=len(fraction_text),
            fraction_separator=fraction_separator or ".",
            time_separator=":",
            leading_colon=leading_colon,
            had_fraction=bool(fraction_text),
            leading_space=leading_space,
            trailing_space=trailing_space,
        )
        return ParsedTimestamp(seconds=seconds, style=style)

    if len(parts) == 3 and all(part.isdigit() for part in parts):
        first_text, second_text, third_text = parts
        first = int(first_text)
        second = int(second_text)
        third = int(third_text)
        if second >= 60:
            return None

        # LRC files commonly use [mm:ss:cc]. Treat a 1-3 digit final field as
        # a fractional second field; otherwise treat the token as [hh:mm:ss].
        if 1 <= len(third_text) <= 3:
            if third >= 10 ** len(third_text):
                return None
            seconds = Decimal(first) * 60 + Decimal(second) + fraction_to_decimal(third_text)
            style = TimestampStyle(
                kind="colon_fraction",
                minute_width=len(first_text),
                second_width=len(second_text),
                fraction_width=len(third_text),
                fraction_separator=":",
                time_separator=":",
                had_fraction=True,
                leading_space=leading_space,
                trailing_space=trailing_space,
            )
            return ParsedTimestamp(seconds=seconds, style=style)

        if third >= 60:
            return None
        seconds = Decimal(first) * 3600 + Decimal(second) * 60 + Decimal(third)
        style = TimestampStyle(
            kind="hours",
            hour_width=len(first_text),
            minute_width=len(second_text),
            second_width=len(third_text),
            time_separator=":",
            leading_space=leading_space,
            trailing_space=trailing_space,
        )
        return ParsedTimestamp(seconds=seconds, style=style)

    return None


def parse_dot_clock_timestamp(core: str, leading_space: str, trailing_space: str) -> ParsedTimestamp | None:
    pieces = re.split(r"([.,])", core)
    values = pieces[0::2]
    separators = pieces[1::2]
    if len(values) != 3 or len(separators) != 2:
        return None
    if not all(value.isdigit() for value in values):
        return None

    minutes_text, seconds_text, fraction_text = values
    whole_seconds = int(seconds_text)
    if whole_seconds >= 60:
        return None

    seconds = Decimal(int(minutes_text)) * 60 + Decimal(whole_seconds) + fraction_to_decimal(fraction_text)
    style = TimestampStyle(
        kind="dot_clock",
        minute_width=len(minutes_text),
        second_width=len(seconds_text),
        fraction_width=len(fraction_text),
        fraction_separator=separators[1],
        time_separator=separators[0],
        had_fraction=True,
        leading_space=leading_space,
        trailing_space=trailing_space,
    )
    return ParsedTimestamp(seconds=seconds, style=style)


def parse_seconds_only_timestamp(core: str, leading_space: str, trailing_space: str) -> ParsedTimestamp | None:
    parsed_seconds = split_seconds_and_fraction(core)
    if parsed_seconds is None:
        return None
    seconds_text, fraction_separator, fraction_text = parsed_seconds
    seconds = Decimal(int(seconds_text)) + fraction_to_decimal(fraction_text)
    style = TimestampStyle(
        kind="seconds",
        second_width=len(seconds_text),
        fraction_width=len(fraction_text),
        fraction_separator=fraction_separator or ".",
        had_fraction=bool(fraction_text),
        leading_space=leading_space,
        trailing_space=trailing_space,
    )
    return ParsedTimestamp(seconds=seconds, style=style)


def parse_timestamp(token: str) -> ParsedTimestamp | None:
    if len(token) > MAX_TIMESTAMP_TOKEN_CHARS:
        return None

    match = re.fullmatch(r"(\s*)(.*?)(\s*)", token)
    if not match:
        return None
    leading_space, core, trailing_space = match.groups()
    if not core:
        return None

    if core.startswith(("+", "-")):
        return None

    if ":" in core:
        return parse_colon_timestamp(core, leading_space, trailing_space)

    dot_clock = parse_dot_clock_timestamp(core, leading_space, trailing_space)
    if dot_clock is not None:
        return dot_clock

    return parse_seconds_only_timestamp(core, leading_space, trailing_space)


def decimal_places(value: Decimal) -> int:
    exponent = value.normalize().as_tuple().exponent
    return max(0, -exponent)


def round_decimal(value: Decimal, places: int) -> Decimal:
    quantizer = Decimal(1).scaleb(-places)
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)


def decimal_fraction_text(value: Decimal, places: int) -> tuple[int, str]:
    rounded = round_decimal(value, places)
    whole = int(rounded)
    fraction = int((rounded - Decimal(whole)) * (Decimal(10) ** places))
    if fraction == 10**places:
        whole += 1
        fraction = 0
    return whole, f"{fraction:0{places}d}" if places else ""


def output_fraction_width(style: TimestampStyle, new_seconds: Decimal) -> int:
    if style.had_fraction:
        return style.fraction_width
    rounded_to_second = round_decimal(new_seconds, 0)
    if rounded_to_second == new_seconds:
        return 0
    return DEFAULT_ADDED_FRACTION_DIGITS


def format_timestamp(seconds: Decimal, style: TimestampStyle) -> str:
    if seconds < 0:
        seconds = Decimal(0)

    places = output_fraction_width(style, seconds)
    rounded = round_decimal(seconds, places)

    if style.kind == "seconds":
        whole, fraction = decimal_fraction_text(rounded, places)
        body = f"{whole:0{style.second_width}d}"
        if places:
            body += f"{style.fraction_separator}{fraction}"
        return f"{style.leading_space}{body}{style.trailing_space}"

    if style.kind == "hours":
        total_seconds = int(round_decimal(rounded, 0))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, whole_seconds = divmod(remainder, 60)
        body = (
            f"{hours:0{style.hour_width}d}"
            f"{style.time_separator}{minutes:0{style.minute_width}d}"
            f"{style.time_separator}{whole_seconds:0{style.second_width}d}"
        )
        return f"{style.leading_space}{body}{style.trailing_space}"

    whole, fraction = decimal_fraction_text(rounded, places)
    minutes, whole_seconds = divmod(whole, 60)

    if style.kind == "colon_fraction":
        body = (
            f"{minutes:0{style.minute_width}d}"
            f"{style.time_separator}{whole_seconds:0{style.second_width}d}"
            f"{style.fraction_separator}{fraction}"
        )
        return f"{style.leading_space}{body}{style.trailing_space}"

    if style.kind == "dot_clock":
        body = (
            f"{minutes:0{style.minute_width}d}"
            f"{style.time_separator}{whole_seconds:0{style.second_width}d}"
        )
        if places:
            body += f"{style.fraction_separator}{fraction}"
        return f"{style.leading_space}{body}{style.trailing_space}"

    if style.leading_colon and minutes == 0:
        body = f"{style.time_separator}{whole_seconds:0{style.second_width}d}"
    else:
        minute_width = style.minute_width or 1
        body = (
            f"{minutes:0{minute_width}d}"
            f"{style.time_separator}{whole_seconds:0{style.second_width}d}"
        )
    if places:
        body += f"{style.fraction_separator}{fraction}"
    return f"{style.leading_space}{body}{style.trailing_space}"


def find_text_timestamps(text: str) -> list[ParsedTimestamp]:
    timestamps: list[ParsedTimestamp] = []
    for match in BRACKETED_TEXT_RE.finditer(text):
        opener, token, closer = match.groups()
        if (opener, closer) not in {("[", "]"), ("<", ">")}:
            continue
        parsed = parse_timestamp(token)
        if parsed is not None:
            timestamps.append(parsed)
    return timestamps


def transform_text(text: str, transform_seconds: Callable[[Decimal], Decimal]) -> tuple[str, int]:
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        opener, token, closer = match.groups()
        if (opener, closer) not in {("[", "]"), ("<", ">")}:
            return match.group(0)
        parsed = parse_timestamp(token)
        if parsed is None:
            return match.group(0)
        changed += 1
        return f"{opener}{format_timestamp(transform_seconds(parsed.seconds), parsed.style)}{closer}"

    return BRACKETED_TEXT_RE.sub(replace, text), changed


def find_bytes_timestamps(data: bytes) -> list[ParsedTimestamp]:
    timestamps: list[ParsedTimestamp] = []
    for match in BRACKETED_BYTES_RE.finditer(data):
        opener, token, closer = match.groups()
        if (opener, closer) not in {(b"[", b"]"), (b"<", b">")}:
            continue
        try:
            token_text = token.decode("ascii")
        except UnicodeDecodeError:
            continue
        parsed = parse_timestamp(token_text)
        if parsed is not None:
            timestamps.append(parsed)
    return timestamps


def transform_bytes_ascii_compatible(
    data: bytes, transform_seconds: Callable[[Decimal], Decimal]
) -> tuple[bytes, int]:
    changed = 0

    def replace(match: re.Match[bytes]) -> bytes:
        nonlocal changed
        opener, token, closer = match.groups()
        if (opener, closer) not in {(b"[", b"]"), (b"<", b">")}:
            return match.group(0)
        try:
            token_text = token.decode("ascii")
        except UnicodeDecodeError:
            return match.group(0)
        parsed = parse_timestamp(token_text)
        if parsed is None:
            return match.group(0)
        changed += 1
        replacement = format_timestamp(transform_seconds(parsed.seconds), parsed.style).encode("ascii")
        return opener + replacement + closer

    return BRACKETED_BYTES_RE.sub(replace, data), changed


def detect_unicode_encoding(data: bytes) -> tuple[str | None, bytes]:
    if data.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le", data[4:]
    if data.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be", data[4:]
    if data.startswith(b"\xff\xfe"):
        return "utf-16-le", data[2:]
    if data.startswith(b"\xfe\xff"):
        return "utf-16-be", data[2:]
    if data.startswith(b"\xef\xbb\xbf"):
        return None, data

    sample = data[: min(len(data), 4096)]
    if len(sample) < 4:
        return None, data

    even_nuls = sample[0::2].count(0)
    odd_nuls = sample[1::2].count(0)
    total_pairs = max(1, len(sample) // 2)
    if odd_nuls / total_pairs > 0.35 and even_nuls / total_pairs < 0.05:
        return "utf-16-le", data
    if even_nuls / total_pairs > 0.35 and odd_nuls / total_pairs < 0.05:
        return "utf-16-be", data

    if len(sample) >= 16:
        lane_counts = [sample[i::4].count(0) for i in range(4)]
        lane_total = max(1, len(sample) // 4)
        if all(lane_counts[i] / lane_total > 0.35 for i in (1, 2, 3)) and lane_counts[0] / lane_total < 0.05:
            return "utf-32-le", data
        if all(lane_counts[i] / lane_total > 0.35 for i in (0, 1, 2)) and lane_counts[3] / lane_total < 0.05:
            return "utf-32-be", data

    return None, data


def transform_data(
    data: bytes, transform_seconds: Callable[[Decimal], Decimal]
) -> tuple[bytes, int, list[ParsedTimestamp]]:
    unicode_encoding, body = detect_unicode_encoding(data)
    if unicode_encoding is None:
        # ASCII-compatible encodings do not need decoding: timestamp syntax is
        # ASCII, and all non-timestamp lyric bytes can be preserved exactly.
        timestamps = find_bytes_timestamps(data)
        new_data, changed = transform_bytes_ascii_compatible(data, transform_seconds)
        return new_data, changed, timestamps

    bom = data[: len(data) - len(body)]
    try:
        text = body.decode(unicode_encoding, errors="strict")
    except UnicodeDecodeError:
        warning(f"Could not decode probable {unicode_encoding}; falling back to byte-safe timestamp scan.")
        timestamps = find_bytes_timestamps(data)
        new_data, changed = transform_bytes_ascii_compatible(data, transform_seconds)
        return new_data, changed, timestamps

    timestamps = find_text_timestamps(text)
    new_text, changed = transform_text(text, transform_seconds)
    return bom + new_text.encode(unicode_encoding), changed, timestamps


def timestamps_from_data(data: bytes) -> list[ParsedTimestamp]:
    unicode_encoding, body = detect_unicode_encoding(data)
    if unicode_encoding is None:
        return find_bytes_timestamps(data)

    try:
        text = body.decode(unicode_encoding, errors="strict")
    except UnicodeDecodeError:
        return find_bytes_timestamps(data)
    return find_text_timestamps(text)


def timestamp_bounds_from_data(data: bytes) -> tuple[Decimal, Decimal] | None:
    timestamps = timestamps_from_data(data)
    if not timestamps:
        return None
    seconds = [timestamp.seconds for timestamp in timestamps]
    return min(seconds), max(seconds)


def final_timestamp_from_data(data: bytes) -> Decimal | None:
    bounds = timestamp_bounds_from_data(data)
    if bounds is None:
        return None
    return bounds[1]


def parse_beginning_end_argument(argument: str) -> tuple[Decimal, Decimal] | None:
    if "," not in argument:
        return None

    parts = argument.split(",")
    if len(parts) != 2:
        return None

    start_text = parts[0].strip()
    end_text = parts[1].strip()
    if ":" not in start_text or ":" not in end_text:
        return None

    parsed_start = parse_timestamp(start_text)
    parsed_end = parse_timestamp(end_text)
    if parsed_start is None or parsed_end is None:
        error(f"Beginning/end timestamps do not look valid: {argument}")
        return None
    return parsed_start.seconds, parsed_end.seconds


def build_transform_plan(
    argument: str, original_start: Decimal, original_final: Decimal
) -> TransformPlan | None:
    parts = argument.split(",")
    looks_like_beginning_end = (
        len(parts) == 2 and ":" in parts[0].strip() and ":" in parts[1].strip()
    )
    beginning_end = parse_beginning_end_argument(argument)
    if looks_like_beginning_end and beginning_end is None:
        return None

    if beginning_end is not None:
        new_start, new_final = beginning_end
        if original_final <= original_start:
            error("Need at least two distinct original timestamps for beginning/end mode.")
            return None
        if new_final <= new_start:
            error(f"New ending timestamp must be after new beginning timestamp: {argument}")
            return None

        original_duration = original_final - original_start
        new_duration = new_final - new_start
        factor = new_duration / original_duration
        slide_seconds = new_start - original_start
        duration_delta = new_duration - original_duration
        backup_label = (
            f"{format_seconds_for_display(slide_seconds, force_sign=True)}_second_slide_"
            f"{format_seconds_for_display(duration_delta, force_sign=True)}_second_stretch"
        )
        return TransformPlan(
            transform_seconds=lambda seconds: new_start + ((seconds - original_start) * factor),
            mode="beginning_end",
            original_start=original_start,
            original_final=original_final,
            new_start=new_start,
            new_final=new_final,
            final_delta=new_final - original_final,
            duration_delta=duration_delta,
            backup_label=backup_label,
        )

    slide_seconds = parse_slide_argument(argument, original_final)
    if slide_seconds is None:
        return None

    new_start = original_start + slide_seconds
    new_final = original_final + slide_seconds
    if new_final <= 0:
        error(
            "Slide would make the final timestamp zero or negative "
            f"({format_seconds_for_display(new_final)} seconds)."
        )
        return None

    if new_start < 0:
        warning(
            "Slide would move the earliest timestamp below zero; affected timestamps "
            "will be clamped to 0."
        )

    backup_label = f"{format_seconds_for_display(slide_seconds, force_sign=True)}_second_slide"
    return TransformPlan(
        transform_seconds=lambda seconds: seconds + slide_seconds,
        mode="slide",
        original_start=original_start,
        original_final=original_final,
        new_start=new_start,
        new_final=new_final,
        final_delta=slide_seconds,
        duration_delta=None,
        backup_label=backup_label,
    )


def parse_slide_argument(argument: str, original_final: Decimal) -> Decimal | None:
    if ":" in argument:
        parsed = parse_timestamp(argument)
        if parsed is None:
            error(f"New final timestamp does not look valid: {argument}")
            return None
        return parsed.seconds - original_final

    slide = parse_seconds_delta_argument(argument)
    if slide is None:
        error(f"Slide amount is not a valid number of seconds: {argument}")
        return None
    return slide


def parse_seconds_delta_argument(argument: str) -> Decimal | None:
    match = SECONDS_DELTA_RE.fullmatch(argument)
    if not match:
        return None
    return parse_decimal(match.group(1).replace(",", "."))


def format_seconds_for_display(value: Decimal, force_sign: bool = False) -> str:
    rounded = value.normalize()
    if rounded == rounded.to_integral():
        text = str(rounded.quantize(Decimal(1)))
    else:
        text = format(rounded, "f").rstrip("0").rstrip(".")
    if force_sign and not text.startswith("-"):
        text = f"+{text}"
    return text


def backup_path_for(path: Path, backup_label: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    candidate = path.with_name(f"{path.stem}.before_{backup_label}.{stamp}.bak")
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        numbered = path.with_name(f"{path.stem}.before_{backup_label}.{stamp}.{counter}.bak")
        if not numbered.exists():
            return numbered
        counter += 1


def write_with_backup(path: Path, original_data: bytes, new_data: bytes, backup_label: str) -> Path | None:
    if new_data == original_data:
        return None
    backup_path = backup_path_for(path, backup_label)
    shutil.copy2(path, backup_path)
    path.write_bytes(new_data)
    return backup_path


def run_self_tests() -> int:
    cases = {
        "30": Decimal("30"),
        ":30": Decimal("30"),
        "0:30": Decimal("30"),
        "00:30.25": Decimal("30.25"),
        "0.30.00": Decimal("30.00"),
        "00:30:25": Decimal("30.25"),
        "ar:The Beatles": None,
        "": None,
    }
    for token, expected in cases.items():
        parsed = parse_timestamp(token)
        got = None if parsed is None else parsed.seconds
        assert got == expected, f"{token!r}: got {got!r}, expected {expected!r}"

    line = b"[00:30]one[0.45.00]two[ar:artist]\xff\n"
    transformed, changed, timestamps = transform_data(line, lambda seconds: seconds * Decimal("2"))
    assert len(timestamps) == 2
    assert changed == 2
    assert transformed == b"[01:00]one[1.30.00]two[ar:artist]\xff\n"

    text = "[00:10.00]a<00:20.00>b[id: nope]"
    transformed_text, changed_text = transform_text(text, lambda seconds: seconds * Decimal("1.5"))
    assert changed_text == 2
    assert transformed_text == "[00:15.00]a<00:30.00>b[id: nope]"

    utf16 = "\ufeff[00:10]hello\n".encode("utf-16")
    transformed_utf16, changed_utf16, timestamps_utf16 = transform_data(
        utf16, lambda seconds: seconds * Decimal("2")
    )
    assert changed_utf16 == 1
    assert len(timestamps_utf16) == 1
    assert transformed_utf16.decode("utf-16") == "\ufeff[00:20]hello\n"

    remap_plan = build_transform_plan("0:30,4:45", Decimal("10"), Decimal("250"))
    assert remap_plan is not None
    assert remap_plan.duration_delta == Decimal("15")
    remap_line = b"[00:10]start\n[02:10]middle\n[04:10]end\n"
    transformed_remap, changed_remap, timestamps_remap = transform_data(
        remap_line, remap_plan.transform_seconds
    )
    assert len(timestamps_remap) == 3
    assert changed_remap == 3
    assert transformed_remap == b"[00:30]start\n[02:37.50]middle\n[04:45]end\n"

    slide_plan = build_transform_plan("-2.5s", Decimal("19"), Decimal("184"))
    assert slide_plan is not None
    assert slide_plan.mode == "slide"
    assert slide_plan.new_start == Decimal("16.5")
    assert slide_plan.new_final == Decimal("181.5")
    assert slide_plan.transform_seconds(Decimal("19")) == Decimal("16.5")
    assert slide_plan.transform_seconds(Decimal("184")) == Decimal("181.5")

    final_timestamp_plan = build_transform_plan("3:01.50", Decimal("19"), Decimal("184"))
    assert final_timestamp_plan is not None
    assert final_timestamp_plan.mode == "slide"
    assert final_timestamp_plan.transform_seconds(Decimal("19")) == Decimal("16.50")
    assert final_timestamp_plan.transform_seconds(Decimal("184")) == Decimal("181.50")

    comma_decimal_plan = build_transform_plan("0:35,22", Decimal("30"), Decimal("60"))
    assert comma_decimal_plan is not None
    assert comma_decimal_plan.new_final == Decimal("35.22")

    print("stretch_lrc.py self-test passed.")
    return EXIT_OK


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--self-test":
        return run_self_tests()

    if len(argv) == 1:
        print(usage())
        return EXIT_OK

    if len(argv) != 3:
        error(f"Expected exactly 2 parameters. Got {argv}")
        print(usage(), file=sys.stderr)
        return EXIT_ERROR

    path = Path(argv[1])
    if not path.exists():
        error(f"Input file does not exist: {path}")
        return EXIT_ERROR
    if not path.is_file():
        error(f"Input path is not a file: {path}")
        return EXIT_ERROR

    try:
        original_data = path.read_bytes()
    except OSError as exc:
        error(f"Could not read input file {path}: {exc}")
        return EXIT_ERROR

    original_bounds = timestamp_bounds_from_data(original_data)
    if original_bounds is None:
        error(f"No recognizable LRC timestamps were found in: {path}")
        return EXIT_ERROR
    original_start, original_final = original_bounds
    if original_final <= 0:
        error(f"The final timestamp is not greater than zero in: {path}")
        return EXIT_ERROR

    transform_plan = build_transform_plan(argv[2], original_start, original_final)
    if transform_plan is None:
        return EXIT_ERROR

    try:
        new_data, changed_count, timestamps = transform_data(original_data, transform_plan.transform_seconds)
    except Exception as exc:
        error(f"Could not process timestamps in {path}: {exc}")
        return EXIT_ERROR

    if not timestamps:
        error(f"No recognizable LRC timestamps were found in: {path}")
        return EXIT_ERROR

    try:
        backup_path = write_with_backup(path, original_data, new_data, transform_plan.backup_label)
    except OSError as exc:
        error(f"Could not write output file or backup for {path}: {exc}")
        return EXIT_ERROR

    delta_display = format_seconds_for_display(transform_plan.final_delta, force_sign=True)
    original_start_display = format_seconds_for_display(original_start)
    new_start_display = (
        format_seconds_for_display(transform_plan.new_start)
        if transform_plan.new_start is not None
        else None
    )
    original_display = format_seconds_for_display(original_final)
    new_display = format_seconds_for_display(transform_plan.new_final)

    if backup_path is None:
        print(
            "No edits were needed "
            f"({changed_count} timestamps inspected; final timestamp stays {original_display}s)."
        )
        return EXIT_OK

    if transform_plan.mode == "beginning_end":
        duration_delta_display = format_seconds_for_display(
            transform_plan.duration_delta or Decimal(0), force_sign=True
        )
        print(
            f"{GREEN}🔄 Remapped: {changed_count} timestamps {FAINT_ON}"
            f"({UNDERLINE_ON}start{UNDERLINE_OFF}: {original_start_display}s -> {ITALICS_ON}{new_start_display}s{ITALICS_OFF}, "
            f"{UNDERLINE_ON}end{UNDERLINE_OFF}: {original_display}s -> {ITALICS_ON}{new_display}s{ITALICS_OFF}; "
            f"duration stretch: {ITALICS_ON}{duration_delta_display}s){ITALICS_OFF}{FAINT_OFF}"
        )
    else:
        print(
            f"{GREEN}➡ Slid:  {changed_count} timestamps {FAINT_ON}by{FAINT_OFF} {delta_display}s {FAINT_ON}"
            f"({UNDERLINE_ON}start{UNDERLINE_Off}: {original_start_display}s -> {ITALICS_ON}{new_start_display}s{ITALICS_OFF}, "
            f"{UNDERLINE_ON}end{UNDERLINE_Off}: {original_display}s -> {ITALICS_ON}{new_display}s{{ITALICS_OFF}}){FAINT_OFF}"
        )
    print(f"{GREEN}{FAINT_ON}🗃  Backup:   {ITALICS_ON}{backup_path}{ITALICS_OFF}{FAINT_OFF}")
    print(f"{BRIGHT_GREEN}✅ Updated:  {GREEN}{ITALICS_ON}{path}{ITALICS_OFF}")
    return EXIT_OK



if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
