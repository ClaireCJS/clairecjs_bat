"""
lrc2srt.py - convert LRC karaoke lyric files to SRT subtitle files.

LRC timestamps mark when a lyric line starts. SRT cues also need an end time.
This converter therefore estimates end times from the sung text instead of
blindly holding every line until the next lyric timestamp.
"""

from __future__ import annotations

import argparse
import codecs
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import wave
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import smartquotes


TOOL_NAME = "lrc2srt"
OUTPUT_EXTENSION = ".srt"
LOG_FILE = Path(r"C:\logs\audiofile-transcription-lrc2srt-conversions.log")
SRT_CONVERTER_NAME = "Claire Sawyer’s LRC2SRT converter"
SRT_CONVERTER_MARKER = "claire-sawyer-lrc2srt-converter-marker"
SRT_COMMENT_BLOCK = (
    f"NOTE Converted with {SRT_CONVERTER_NAME}\n"
    f"NOTE {SRT_CONVERTER_MARKER}: generated-from-lrc\n\n"
)

# Tuned to be a little generous for sung lyrics without letting one lyric line
# sit on screen for an entire instrumental break.
DEFAULT_SECONDS_PER_WORD = 0.55
DEFAULT_SECONDS_PER_SYLLABLE = 0.12
DEFAULT_LINE_PADDING_SECONDS = 0.55
DEFAULT_PUNCTUATION_PAUSE_SECONDS = 0.18
DEFAULT_MIN_DURATION_SECONDS = 1.25
DEFAULT_MAX_DURATION_SECONDS = 8.00
DEFAULT_MAX_BLANK_END_MARKER_DURATION_SECONDS = 12.00
DEFAULT_GAP_BEFORE_NEXT_LINE_SECONDS = 0.08
DEFAULT_MERGE_CUES_WITHIN_SECONDS = 0.35
DEFAULT_LINE_WIDTH = 25
AUTO_AUDIO_DURATION_CAP_SURVEY_PERCENT = 2
AUDIO_SIDECAR_EXTENSIONS = (
    ".flac",
    ".mp3",
    ".wav",
    ".wave",
    ".m4a",
    ".aac",
    ".ogg",
    ".opus",
    ".wma",
    ".aiff",
    ".aif",
)
SELF_TEST_RECYCLED_ROOT = Path(r"C:\recycled")

TIMESTAMP_REGEX = re.compile(
    r"\[((?:\d+:)?\d{1,2}:\d{2}(?:[\.,]\d{1,3})?)\]"
)
WORD_REGEX = re.compile(r"[^\W_]+(?:['\u2019-][^\W_]+)*", re.UNICODE)
VOWEL_GROUP_REGEX = re.compile(r"[aeiouy]+")


@dataclass(frozen=True)
class LrcEvent:
    time_seconds: float
    text: str
    source_line_number: int
    sequence: int


@dataclass(frozen=True)
class SrtCue:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass
class ConversionOptions:
    force: bool = False
    automatic_overwrites: bool = False
    dry_run: bool = False
    seconds_per_word: float = DEFAULT_SECONDS_PER_WORD
    seconds_per_syllable: float = DEFAULT_SECONDS_PER_SYLLABLE
    line_padding_seconds: float = DEFAULT_LINE_PADDING_SECONDS
    punctuation_pause_seconds: float = DEFAULT_PUNCTUATION_PAUSE_SECONDS
    min_duration_seconds: float = DEFAULT_MIN_DURATION_SECONDS
    max_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS
    max_blank_end_marker_duration_seconds: float | None = (
        DEFAULT_MAX_BLANK_END_MARKER_DURATION_SECONDS
    )
    gap_before_next_line_seconds: float = DEFAULT_GAP_BEFORE_NEXT_LINE_SECONDS
    merge_cues_within_seconds: float = DEFAULT_MERGE_CUES_WITHIN_SECONDS
    line_width: int = DEFAULT_LINE_WIDTH
    wrap_lines: bool = True
    song_length_seconds: float | None = None


@dataclass(frozen=True)
class ConversionResult:
    input_file: Path
    output_file: Path
    cue_count: int
    skipped: bool = False
    backup_file: Path | None = None
    dry_run: bool = False
    review_approved: bool | None = None
    reason: str = "convert"


@dataclass(frozen=True)
class ConversionTask:
    input_file: Path
    output_file: Path
    reason: str = "convert"


@dataclass(frozen=True)
class AudioDurationProbe:
    audio_file: Path
    duration_seconds: float
    applied: bool
    reason: str


LOG_WARNING_ALREADY_PRINTED = False


def log_event(action: str, **details: Any) -> None:
    """Append one JSONL record to the always-on converter log."""
    global LOG_WARNING_ALREADY_PRINTED
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "tool": TOOL_NAME,
        "action": action,
        **details,
    }

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:
        if not LOG_WARNING_ALREADY_PRINTED:
            print_warning(f"       * WARNING: could not write log file '{LOG_FILE}': {exc}")
            LOG_WARNING_ALREADY_PRINTED = True


def prompt_yes_no(question: str, default: bool) -> bool:
    default_label = "Y/n" if default else "y/N"
    if not sys.stdin.isatty():
        print_warning(
            f"       * Non-interactive session: defaulting to "
            f"{'YES' if default else 'NO'} for: {question}"
        )
        return default

    while True:
        answer = input(
            console_safe_text(output_color(f"{question} [{default_label}] ", ANSI_YELLOW))
        ).strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print_warning("Please answer yes or no.")


def unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        key = re.sub(r"\s+", " ", value).strip().casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output


def parse_timestamp(timestamp: str) -> float:
    """Parse MM:SS.xx or HH:MM:SS.xx into seconds."""
    value = timestamp.strip().strip("[]").replace(",", ".")
    parts = value.split(":")

    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds

    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    raise ValueError(f"Unsupported timestamp: {timestamp}")


def parse_duration_or_timestamp(value: str) -> float:
    """Accept raw seconds, MM:SS.xx, HH:MM:SS.xx, or bracketed LRC time."""
    stripped = value.strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", stripped):
        return float(stripped)
    return parse_timestamp(stripped)


def format_srt_timestamp(seconds: float) -> str:
    total_milliseconds = int(round(max(0.0, seconds) * 1000))
    milliseconds = total_milliseconds % 1000
    total_seconds = total_milliseconds // 1000
    seconds_part = total_seconds % 60
    total_minutes = total_seconds // 60
    minutes_part = total_minutes % 60
    hours_part = total_minutes // 60
    return f"{hours_part:02}:{minutes_part:02}:{seconds_part:02},{milliseconds:03}"


def candidate_encodings(raw_bytes: bytes) -> list[str]:
    encodings = []

    if raw_bytes.startswith(codecs.BOM_UTF8):
        encodings.append("utf-8-sig")
    elif raw_bytes.startswith(codecs.BOM_UTF16_LE):
        encodings.append("utf-16-le")
    elif raw_bytes.startswith(codecs.BOM_UTF16_BE):
        encodings.append("utf-16-be")

    try:
        import chardet  # type: ignore

        detected = chardet.detect(raw_bytes[:8192]).get("encoding")
        if detected:
            encodings.append(detected)
    except Exception:
        pass

    encodings.extend(["utf-8-sig", "utf-8", "cp1252", "latin-1"])

    unique = []
    for encoding in encodings:
        normalized = encoding.lower()
        if normalized not in [item.lower() for item in unique]:
            unique.append(encoding)
    return unique


def read_text_file(path: Path) -> tuple[str, str]:
    raw_bytes = path.read_bytes()

    for encoding in candidate_encodings(raw_bytes):
        try:
            return raw_bytes.decode(encoding), encoding
        except UnicodeDecodeError:
            continue

    return raw_bytes.decode("utf-8", errors="replace"), "utf-8-replace"


def normalize_lrc_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\\n", "\n")
    text = text.replace("\\N", "\n")
    text = smartquotes.smartify_quotes(text)
    text = re.sub(r"[ \t]+", " ", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def parse_lrc_lines(lines: Iterable[str]) -> list[LrcEvent]:
    events: list[LrcEvent] = []
    sequence = 0

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip("\r\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        timestamp_matches = list(TIMESTAMP_REGEX.finditer(line))
        if not timestamp_matches:
            continue

        text = normalize_lrc_text(TIMESTAMP_REGEX.sub("", line))
        for match in timestamp_matches:
            sequence += 1
            events.append(
                LrcEvent(
                    time_seconds=parse_timestamp(match.group(1)),
                    text=text,
                    source_line_number=line_number,
                    sequence=sequence,
                )
            )

    return sorted(
        events,
        key=lambda event: (
            event.time_seconds,
            event.source_line_number,
            event.sequence,
        ),
    )


def parse_lrc_file(path: Path) -> tuple[list[LrcEvent], str]:
    text, encoding = read_text_file(path)
    return parse_lrc_lines(text.splitlines()), encoding


def estimate_syllables_for_word(word: str) -> int:
    letters = re.sub(r"[^a-z]", "", word.lower())
    if not letters:
        return 1

    groups = VOWEL_GROUP_REGEX.findall(letters)
    syllables = len(groups)

    if letters.endswith("e") and not letters.endswith(("le", "ye")) and syllables > 1:
        syllables -= 1

    if letters.endswith("le") and len(letters) > 2 and letters[-3] not in "aeiouy":
        syllables += 1

    return max(1, syllables)


def estimate_line_duration_seconds(text: str, options: ConversionOptions) -> float:
    words = WORD_REGEX.findall(text)
    word_count = len(words)
    syllable_count = sum(estimate_syllables_for_word(word) for word in words)
    punctuation_count = len(re.findall(r"[,.!?;:]", text))

    if word_count == 0:
        return max(0.20, options.min_duration_seconds)

    duration = (
        options.line_padding_seconds
        + word_count * options.seconds_per_word
        + syllable_count * options.seconds_per_syllable
        + min(0.90, punctuation_count * options.punctuation_pause_seconds)
    )

    return min(
        max(duration, options.min_duration_seconds),
        options.max_duration_seconds,
    )


def wrap_srt_text(text: str, line_width: int) -> str:
    if line_width <= 0:
        return text

    wrapped_lines: list[str] = []
    for logical_line in text.splitlines() or [text]:
        wrapped = textwrap.wrap(
            logical_line,
            width=line_width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        wrapped_lines.extend(wrapped or [""])
    return "\n".join(wrapped_lines)


def build_srt_cues(events: list[LrcEvent], options: ConversionOptions) -> list[SrtCue]:
    cues: list[SrtCue] = []
    index = 0

    while index < len(events):
        start_time = events[index].time_seconds
        grouped_events: list[LrcEvent] = []

        while index < len(events):
            event = events[index]
            same_timestamp = abs(event.time_seconds - start_time) < 0.0005
            nearby_text_timestamp = (
                bool(event.text.strip())
                and options.merge_cues_within_seconds > 0
                and event.time_seconds - start_time <= options.merge_cues_within_seconds
            )
            if grouped_events and not (same_timestamp or nearby_text_timestamp):
                break
            grouped_events.append(event)
            index += 1

        grouped_texts = [
            event.text for event in grouped_events if event.text.strip()
        ]
        if not grouped_texts:
            continue

        text = "\n".join(unique_preserving_order(grouped_texts))
        estimated_end = start_time + estimate_line_duration_seconds(text, options)
        following_event = events[index] if index < len(events) else None
        following_text_event = None
        for lookahead_event in events[index:]:
            if lookahead_event.text.strip():
                following_text_event = lookahead_event
                break

        if following_event and not following_event.text.strip():
            explicit_end_time = following_event.time_seconds
            blank_marker_duration = explicit_end_time - start_time
            blank_marker_is_too_far = (
                options.max_blank_end_marker_duration_seconds is not None
                and blank_marker_duration
                > options.max_blank_end_marker_duration_seconds
            )
            blank_marker_is_too_close = (
                blank_marker_duration < options.min_duration_seconds
            )
            if blank_marker_is_too_far or blank_marker_is_too_close:
                end_time = estimated_end
                if following_text_event:
                    end_time = min(
                        end_time,
                        following_text_event.time_seconds
                        - options.gap_before_next_line_seconds,
                    )
            else:
                end_time = explicit_end_time
        elif following_event and following_event.text.strip():
            latest_end_before_next = (
                following_event.time_seconds - options.gap_before_next_line_seconds
            )
            end_time = min(estimated_end, latest_end_before_next)
        else:
            end_time = estimated_end

        if options.song_length_seconds is not None:
            end_time = min(end_time, options.song_length_seconds)

        if end_time <= start_time:
            if following_event and following_event.time_seconds > start_time:
                end_time = max(
                    start_time + 0.001,
                    following_event.time_seconds - 0.001,
                )
            else:
                end_time = start_time + 0.001

        if options.wrap_lines:
            text = wrap_srt_text(text, options.line_width)

        cues.append(SrtCue(start_time, end_time, text))

    return cues


def render_srt(cues: list[SrtCue], include_converter_comment: bool = True) -> str:
    blocks = []
    for cue_number, cue in enumerate(cues, start=1):
        blocks.append(
            "\n".join(
                [
                    str(cue_number),
                    (
                        f"{format_srt_timestamp(cue.start_seconds)} --> "
                        f"{format_srt_timestamp(cue.end_seconds)}"
                    ),
                    cue.text,
                ]
            )
        )
    rendered_cues = "\n\n".join(blocks) + ("\n" if blocks else "")
    if include_converter_comment:
        return SRT_COMMENT_BLOCK + rendered_cues
    return rendered_cues


def lrc_text_to_srt(lrc_text: str, options: ConversionOptions) -> str:
    events = parse_lrc_lines(lrc_text.splitlines())
    cues = build_srt_cues(events, options)
    return render_srt(cues)


def srt_text_was_created_by_this_tool(text: str) -> bool:
    return SRT_CONVERTER_MARKER in text[:4096]


def srt_file_was_created_by_this_tool(path: Path) -> bool:
    if not path.exists():
        return False
    text, _ = read_text_file(path)
    return srt_text_was_created_by_this_tool(text)


def find_audio_sidecar_file(lrc_file: Path) -> Path | None:
    extension_priority = {
        extension.casefold(): index
        for index, extension in enumerate(AUDIO_SIDECAR_EXTENSIONS)
    }
    stem_key = lrc_file.stem.casefold()
    candidates: list[Path] = []

    for extension in AUDIO_SIDECAR_EXTENSIONS:
        candidate = lrc_file.with_suffix(extension)
        if candidate.exists() and candidate.is_file():
            candidates.append(candidate)

    try:
        for candidate in lrc_file.parent.iterdir():
            if (
                candidate.is_file()
                and candidate.stem.casefold() == stem_key
                and candidate.suffix.casefold() in extension_priority
            ):
                candidates.append(candidate)
    except OSError:
        return None

    unique_candidates = []
    seen = set()
    for candidate in candidates:
        key = str(candidate.resolve()).casefold()
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(candidate)

    if not unique_candidates:
        return None

    return sorted(
        unique_candidates,
        key=lambda path: extension_priority.get(path.suffix.casefold(), 999),
    )[0]


def probe_wav_duration_seconds(audio_file: Path) -> float | None:
    try:
        with wave.open(str(audio_file), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
    except (EOFError, OSError, wave.Error):
        return None

    if frame_rate <= 0:
        return None
    return frame_count / frame_rate


def probe_audio_duration_seconds(audio_file: Path) -> float | None:
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        try:
            result = subprocess.run(
                [
                    ffprobe_path,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio_file),
                ],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            result = None

        if result and result.returncode == 0:
            try:
                duration = float(result.stdout.strip().splitlines()[0])
            except (IndexError, ValueError):
                duration = 0.0
            if duration > 0:
                return duration

    if audio_file.suffix.casefold() in {".wav", ".wave"}:
        return probe_wav_duration_seconds(audio_file)

    return None


def final_cue_may_need_song_length_cap(
    events: list[LrcEvent],
    cues: list[SrtCue],
    options: ConversionOptions,
) -> bool:
    if not cues:
        return False

    last_text_event_index = None
    for index, event in enumerate(events):
        if event.text.strip():
            last_text_event_index = index

    if last_text_event_index is None:
        return False

    last_text_event = events[last_text_event_index]
    for following_event in events[last_text_event_index + 1 :]:
        if following_event.text.strip():
            return False
        explicit_end_duration = following_event.time_seconds - last_text_event.time_seconds
        explicit_end_is_close_enough = (
            explicit_end_duration >= options.min_duration_seconds
            and (
                options.max_blank_end_marker_duration_seconds is None
                or explicit_end_duration
                <= options.max_blank_end_marker_duration_seconds
            )
        )
        if explicit_end_is_close_enough:
            return False
        return True

    return cues[-1].end_seconds > cues[-1].start_seconds


def probe_audio_song_length_if_needed(
    input_file: Path,
    events: list[LrcEvent],
    cues: list[SrtCue],
    options: ConversionOptions,
) -> AudioDurationProbe | None:
    if options.song_length_seconds is not None:
        return None

    if not final_cue_may_need_song_length_cap(events, cues, options):
        log_event(
            "audio_duration_probe_skipped_not_needed",
            input_file=str(input_file),
            reason="final_lyric_has_explicit_or_following_end",
        )
        return None

    audio_file = find_audio_sidecar_file(input_file)
    if audio_file is None:
        log_event(
            "audio_duration_probe_skipped_missing_sidecar",
            input_file=str(input_file),
        )
        return None

    duration = probe_audio_duration_seconds(audio_file)
    if duration is None:
        log_event(
            "audio_duration_probe_failed",
            input_file=str(input_file),
            audio_file=str(audio_file),
        )
        return None

    final_cue = cues[-1]
    if not (final_cue.start_seconds < duration < final_cue.end_seconds - 0.05):
        log_event(
            "audio_duration_probe_not_needed",
            input_file=str(input_file),
            audio_file=str(audio_file),
            audio_duration_seconds=round(duration, 3),
            final_cue_end_seconds=round(final_cue.end_seconds, 3),
        )
        return AudioDurationProbe(
            audio_file=audio_file,
            duration_seconds=duration,
            applied=False,
            reason="final_estimate_within_audio_duration",
        )

    log_event(
        "audio_duration_probe_applied",
        input_file=str(input_file),
        audio_file=str(audio_file),
        audio_duration_seconds=round(duration, 3),
        original_final_cue_end_seconds=round(final_cue.end_seconds, 3),
    )
    return AudioDurationProbe(
        audio_file=audio_file,
        duration_seconds=duration,
        applied=True,
        reason="final_estimate_exceeded_audio_duration",
    )


def default_output_path_for(input_file: Path) -> Path:
    if input_file.suffix.lower() == ".lrc":
        return input_file.with_suffix(OUTPUT_EXTENSION)
    return Path(f"{input_file}{OUTPUT_EXTENSION}")


def backup_path_for_replaced_file(path: Path) -> Path:
    date_stamp = datetime.now().strftime("%Y%m%d")
    first_choice = Path(f"{path}.bak.{date_stamp}.replaced-by-{TOOL_NAME}.bak")
    if not first_choice.exists():
        return first_choice

    for counter in range(2, 1000):
        candidate = Path(
            f"{path}.bak.{date_stamp}.{counter:03}.replaced-by-{TOOL_NAME}.bak"
        )
        if not candidate.exists():
            return candidate

    raise RuntimeError(f"Too many backup files already exist for {path}")


def preview_srt_text(srt_text: str, max_lines: int = 16) -> str:
    lines = srt_text.splitlines()
    preview = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        preview += "\n..."
    return preview


def review_conversion_result(
    output_file: Path,
    srt_text: str,
    options: ConversionOptions,
) -> bool | None:
    if options.automatic_overwrites:
        return None

    print_info(f"       * Review: {output_file}")
    print(textwrap.indent(preview_srt_text(srt_text), "         "))
    print_warning(
        "       * Does this look good? "
        "Use --automatic-overwrites to suppress this prompt."
    )
    approved = prompt_yes_no("       * Does this look good?", default=True)
    log_event(
        "review_answer",
        output_file=str(output_file),
        approved=approved,
    )
    if not approved:
        print_warning(
            "       * Review was not approved. The generated file remains in "
            "place; any replaced file was already preserved as a backup."
        )
    return approved


def convert_lrc_file(
    input_file: Path,
    output_file: Path | None,
    options: ConversionOptions,
    reason: str = "convert",
) -> ConversionResult:
    resolved_output_file = output_file or default_output_path_for(input_file)
    events, encoding = parse_lrc_file(input_file)
    cues = build_srt_cues(events, options)
    audio_duration_probe = probe_audio_song_length_if_needed(
        input_file,
        events,
        cues,
        options,
    )
    effective_options = options
    song_length_source = "manual" if options.song_length_seconds is not None else None
    if audio_duration_probe and audio_duration_probe.applied:
        effective_options = replace(
            options,
            song_length_seconds=audio_duration_probe.duration_seconds,
        )
        cues = build_srt_cues(events, effective_options)
        song_length_source = "audio-sidecar"
    srt_text = render_srt(cues)

    log_event(
        "conversion_started",
        input_file=str(input_file),
        output_file=str(resolved_output_file),
        reason=reason,
        encoding=encoding,
        cue_count=len(cues),
        dry_run=options.dry_run,
        automatic_overwrites=options.automatic_overwrites,
        song_length_seconds=(
            round(effective_options.song_length_seconds, 3)
            if effective_options.song_length_seconds is not None
            else None
        ),
        song_length_source=song_length_source,
        audio_duration_probe=(
            {
                "audio_file": str(audio_duration_probe.audio_file),
                "duration_seconds": round(audio_duration_probe.duration_seconds, 3),
                "applied": audio_duration_probe.applied,
                "reason": audio_duration_probe.reason,
            }
            if audio_duration_probe
            else None
        ),
    )

    backup_file = None
    if resolved_output_file.exists():
        if not (options.force or options.automatic_overwrites):
            print_warning(
                f"       * WARNING: SRT '{resolved_output_file}' already exists."
            )
            print_warning(
                "       * It will be backed up before replacement. "
                "Use --automatic-overwrites to skip this prompt."
            )
            should_replace = prompt_yes_no(
                f"       * Replace '{resolved_output_file}'?",
                default=False,
            )
            log_event(
                "overwrite_prompt_answer",
                input_file=str(input_file),
                output_file=str(resolved_output_file),
                approved=should_replace,
            )
            if not should_replace:
                print_warning(f"       * Skipping: {resolved_output_file}")
                log_event(
                    "conversion_skipped_existing_output",
                    input_file=str(input_file),
                    output_file=str(resolved_output_file),
                    reason=reason,
                )
                return ConversionResult(
                    input_file=input_file,
                    output_file=resolved_output_file,
                    cue_count=len(cues),
                    skipped=True,
                    dry_run=options.dry_run,
                    reason=reason,
                )

        backup_file = backup_path_for_replaced_file(resolved_output_file)
        if options.dry_run:
            print_info(
                f"       * DRY RUN: would back up '{resolved_output_file}' as "
                f"'{backup_file}'"
            )
        else:
            os.rename(resolved_output_file, backup_file)
            print_warning(
                f"       * WARNING: SRT '{resolved_output_file}' already existed - "
                f"backed up as '{backup_file}'"
            )
        log_event(
            "output_backed_up",
            input_file=str(input_file),
            output_file=str(resolved_output_file),
            backup_file=str(backup_file),
            dry_run=options.dry_run,
        )

    if options.dry_run:
        print_info(
            f"       * DRY RUN: would convert '{input_file}' ({encoding}) to "
            f"'{resolved_output_file}' with {len(cues)} cues"
        )
        log_event(
            "conversion_dry_run",
            input_file=str(input_file),
            output_file=str(resolved_output_file),
            cue_count=len(cues),
            reason=reason,
        )
    else:
        resolved_output_file.write_text(srt_text, encoding="utf-8")
        log_event(
            "conversion_written",
            input_file=str(input_file),
            output_file=str(resolved_output_file),
            cue_count=len(cues),
            reason=reason,
            backup_file=str(backup_file) if backup_file else None,
        )

    review_approved = None
    if not options.dry_run:
        review_approved = review_conversion_result(
            resolved_output_file,
            srt_text,
            options,
        )

    return ConversionResult(
        input_file=input_file,
        output_file=resolved_output_file,
        cue_count=len(cues),
        skipped=False,
        backup_file=backup_file,
        dry_run=options.dry_run,
        review_approved=review_approved,
        reason=reason,
    )


def pattern_has_wildcards(pattern: str) -> bool:
    return any(character in pattern for character in "*?[")


def expand_files(
    patterns: list[str],
    default_pattern: str,
    recursive: bool,
) -> list[Path]:
    effective_patterns = patterns or [default_pattern]
    files: list[Path] = []

    for pattern in effective_patterns:
        literal_path = Path(pattern)
        matches: list[Path] = []

        if literal_path.exists():
            if literal_path.is_dir():
                if recursive:
                    matches = list(literal_path.rglob(default_pattern))
                else:
                    matches = list(literal_path.glob(default_pattern))
            else:
                matches = [literal_path]
        elif recursive and not Path(pattern).is_absolute():
            # Keep the search root literal. glob.glob(str(Path.cwd() / "**" / pattern))
            # misreads cwd brackets like "[live]" as glob syntax.
            matches = list(Path.cwd().rglob(pattern.replace("\\", "/")))
        else:
            matches = [Path(match) for match in glob.glob(pattern, recursive=recursive)]

        file_matches = [match for match in matches if match.is_file()]
        if file_matches:
            files.extend(file_matches)
        else:
            print_warning(f"?! No files matched pattern: {pattern}")
            log_event("pattern_matched_no_files", pattern=pattern, recursive=recursive)

    unique_files = []
    seen = set()
    for file_path in files:
        key = str(file_path.resolve()).casefold()
        if key in seen:
            continue
        seen.add(key)
        unique_files.append(file_path)

    return sorted(unique_files, key=lambda path: str(path.resolve()).casefold())


def build_lrc_tasks(
    patterns: list[str],
    process_all: bool,
    recursive: bool,
    output_file: str | None,
) -> list[ConversionTask]:
    input_files = expand_files(
        [] if process_all else patterns,
        "*.lrc",
        recursive,
    )

    if output_file and len(input_files) > 1:
        raise ValueError("Cannot specify --output when converting multiple files.")

    return [
        ConversionTask(
            input_file=input_file,
            output_file=Path(output_file) if output_file else default_output_path_for(input_file),
            reason="convert",
        )
        for input_file in input_files
        if input_file.suffix.lower() == ".lrc"
    ]


def build_minilyricsfix_tasks(
    patterns: list[str],
    recursive: bool,
) -> list[ConversionTask]:
    input_files = expand_files(patterns, "*.lrc", recursive)
    tasks: list[ConversionTask] = []
    missing_txt_count = 0
    existing_srt_count = 0
    non_lrc_count = 0

    for input_file in input_files:
        if input_file.suffix.lower() != ".lrc":
            non_lrc_count += 1
            continue

        txt_file = input_file.with_suffix(".txt")
        srt_file = input_file.with_suffix(".srt")

        if not txt_file.exists():
            missing_txt_count += 1
            log_event(
                "minilyricsfix_skipped_missing_txt",
                input_file=str(input_file),
                expected_txt=str(txt_file),
            )
            continue

        if srt_file.exists():
            existing_srt_count += 1
            log_event(
                "minilyricsfix_skipped_existing_srt",
                input_file=str(input_file),
                existing_srt=str(srt_file),
            )
            continue

        tasks.append(
            ConversionTask(
                input_file=input_file,
                output_file=srt_file,
                reason="MiniLyricsFix",
            )
        )

    print_info(
        "    * MiniLyricsFix scan: "
        f"{len(tasks)} eligible; "
        f"{missing_txt_count} missing TXT; "
        f"{existing_srt_count} already had SRT."
    )
    log_event(
        "minilyricsfix_scan_completed",
        eligible=len(tasks),
        missing_txt=missing_txt_count,
        existing_srt=existing_srt_count,
        non_lrc=non_lrc_count,
        recursive=recursive,
    )
    return tasks


def build_regeneration_tasks(
    patterns: list[str],
    recursive: bool,
    converted_only: bool,
) -> list[ConversionTask]:
    srt_files = expand_files(patterns, "*.srt", recursive)
    tasks: list[ConversionTask] = []

    for srt_file in srt_files:
        if srt_file.suffix.lower() != ".srt":
            continue

        was_created_here = srt_file_was_created_by_this_tool(srt_file)
        if converted_only and not was_created_here:
            print_warning(f"    * Skipping SRT not created by this tool: {srt_file}")
            log_event(
                "regeneration_skipped_not_created_by_tool",
                srt_file=str(srt_file),
            )
            continue

        lrc_file = srt_file.with_suffix(".lrc")
        if not lrc_file.exists():
            print_warning(f"    * Skipping SRT with no LRC sidecar: {srt_file}")
            log_event(
                "regeneration_skipped_missing_lrc",
                srt_file=str(srt_file),
                expected_lrc=str(lrc_file),
            )
            continue

        tasks.append(
            ConversionTask(
                input_file=lrc_file,
                output_file=srt_file,
                reason=(
                    "regenerate-converted-srts"
                    if converted_only
                    else "regenerate-all-srts"
                ),
            )
        )

    return tasks


def print_folder_header_if_needed(
    task: ConversionTask,
    last_folder: Path | None,
    show_headers: bool,
) -> Path:
    folder = task.input_file.parent.resolve()
    if show_headers and folder != last_folder:
        print()
        print_folder_header(f"=== Folder: {folder} ===")
        log_event("folder_started", folder=str(folder))
    return folder


def run_conversion_tasks(
    tasks: list[ConversionTask],
    options: ConversionOptions,
    show_folder_headers: bool,
) -> list[ConversionResult]:
    results = []
    last_folder = None

    for task in tasks:
        last_folder = print_folder_header_if_needed(task, last_folder, show_folder_headers)
        print_info(f"    * Converting: {task.input_file}")
        result = convert_lrc_file(
            task.input_file,
            task.output_file,
            options,
            reason=task.reason,
        )
        results.append(result)

        if result.skipped:
            print_warning(f"       * Finished skipped: {result.output_file}")
        elif result.dry_run:
            print_info(f"       * Finished dry run: {result.output_file}")
        else:
            print_success(
                f"       * Finished: {result.output_file} "
                f"({result.cue_count} cues)"
            )

    return results


def validate_options(options: ConversionOptions) -> None:
    numeric_values = {
        "seconds_per_word": options.seconds_per_word,
        "seconds_per_syllable": options.seconds_per_syllable,
        "line_padding_seconds": options.line_padding_seconds,
        "punctuation_pause_seconds": options.punctuation_pause_seconds,
        "min_duration_seconds": options.min_duration_seconds,
        "max_duration_seconds": options.max_duration_seconds,
        "gap_before_next_line_seconds": options.gap_before_next_line_seconds,
        "merge_cues_within_seconds": options.merge_cues_within_seconds,
    }

    for name, value in numeric_values.items():
        if value < 0:
            raise ValueError(f"{name} must not be negative")

    if options.max_duration_seconds <= 0:
        raise ValueError("max_duration_seconds must be positive")

    if options.min_duration_seconds > options.max_duration_seconds:
        raise ValueError("min_duration_seconds must not exceed max_duration_seconds")

    if (
        options.max_blank_end_marker_duration_seconds is not None
        and options.max_blank_end_marker_duration_seconds <= 0
    ):
        raise ValueError("max_blank_end_marker_duration_seconds must be positive")

    if options.line_width < 1 and options.wrap_lines:
        raise ValueError("line_width must be at least 1 unless --no-wrap is used")


ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_BLINK = "\033[5m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[96m"
ANSI_GREEN = "\033[92m"
ANSI_MAGENTA = "\033[95m"
ANSI_BLUE = "\033[94m"
ANSI_YELLOW = "\033[93m"
ANSI_RED = "\033[91m"
ANSI_DOUBLE_HEIGHT_TOP = "\033#3"
ANSI_DOUBLE_HEIGHT_BOTTOM = "\033#4"


def output_color(text: str, color: str, extra_style: str = "") -> str:
    return f"{extra_style}{color}{text}{ANSI_RESET}"


def print_colored(text: str, color: str, extra_style: str = "") -> None:
    print(console_safe_text(output_color(text, color, extra_style)))


def print_info(text: str) -> None:
    print_colored(text, ANSI_CYAN)


def print_success(text: str) -> None:
    print_colored(text, ANSI_GREEN, ANSI_BOLD)


def print_warning(text: str) -> None:
    print_colored(text, ANSI_YELLOW)


def print_error(text: str) -> None:
    print_colored(text, ANSI_RED, ANSI_BOLD)


def print_folder_header(text: str) -> None:
    print_colored(text, ANSI_BLUE, ANSI_BOLD)


def usage_cli(text: str) -> str:
    return f"{ANSI_CYAN}{text}{ANSI_RESET}"


def usage_example_value(text: str) -> str:
    return f"{ANSI_BLUE}{text}{ANSI_RESET}"


def usage_note(text: str) -> str:
    return f"{ANSI_DIM}{ANSI_YELLOW}{text}{ANSI_RESET}"


def usage_command(*parts: tuple[str, str]) -> str:
    styles = {
        "cli": ANSI_CYAN,
        "example": ANSI_BLUE,
        "special_mode": f"{ANSI_BLINK}{ANSI_CYAN}",
    }
    rendered = []
    for part_type, text in parts:
        rendered.append(f"{styles[part_type]}{text}{ANSI_RESET}")
    return "  " + "".join(rendered)


def usage_double_height_header(text: str, color: str, extra_style: str = "") -> list[str]:
    return [
        f"{ANSI_BOLD}{extra_style}{color}{ANSI_DOUBLE_HEIGHT_TOP}{text}{ANSI_RESET}",
        f"{ANSI_BOLD}{extra_style}{color}{ANSI_DOUBLE_HEIGHT_BOTTOM}{text}{ANSI_RESET}",
    ]


def render_usage() -> str:
    title_header_text = "\u2728\u2731\u2728 lrc2srt \u2728\u2731\u2728"
    header_text = "\u2728\u2731\u2728 Usage: \u2728\u2731\u2728"
    flags_header_text = "\u2728\u2731\u2728 Flags: \u2728\u2731\u2728"
    modes_header_text = "\u2728\u2731\u2728 Modes: \u2728\u2731\u2728"
    examples_header_text = "\u2728\u2731\u2728 Examples: \u2728\u2731\u2728"
    logging_header_text = "\u2728\u2731\u2728 Logging: \u2728\u2731\u2728"

    return "\n".join(
        [
            "",
            *usage_double_height_header(title_header_text, ANSI_GREEN, ANSI_BLINK),
            "",
            usage_note(
                "  Conversion of timed lyric/subtitle files from LRC format "
                "to SRT format, including estimating the end timestamps for "
                "each lyric, which exist in SRT but not in LRC."
            ),
            "",
            *usage_double_height_header(header_text, ANSI_GREEN),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("example", "song.lrc"),
                ("cli", " ["),
                ("example", "more.lrc ..."),
                ("cli", "] [flags]"),
            ),
            usage_note(
                "  ^ Convert one or more named LRC files; add any flags below "
                "when you want batch behavior, recursion, or duration tuning."
            ),
            "",
            *usage_double_height_header(flags_header_text, ANSI_GREEN),
            "",
            usage_command(("cli", "--automatic-overwrites")),
            usage_note(
                "  ^ Back up and replace existing SRT files without pausing "
                "for overwrite or review prompts."
            ),
            "",
            usage_command(("cli", "-f  --force  force")),
            usage_note(
                "  ^ Legacy aliases for --automatic-overwrites; kept for old "
                "batch habits, but --automatic-overwrites is clearer."
            ),
            "",
            usage_command(("cli", "-a  --all")),
            usage_note(
                "  ^ Same as the all mode: convert every *.lrc file in the "
                "current folder."
            ),
            "",
            usage_command(("cli", "-r  --recursive")),
            usage_note(
                "  ^ Include subfolders when expanding wildcards or the all, "
                "go, MiniLyricsFix, and regeneration modes. For multi-folder "
                "batches, print a folder header before that folder's files."
            ),
            "",
            usage_command(("cli", "--seconds-per-word "), ("example", "0.65")),
            usage_note(
                "  ^ Estimate lyric cue length from sung word count when the "
                "LRC has no end timestamps; higher values keep lines onscreen "
                "longer."
            ),
            "",
            usage_command(
                ("cli", "--seconds-per-syllable "),
                ("example", "0.08"),
                ("cli", "  --line-padding "),
                ("example", "0.20"),
            ),
            usage_command(
                ("cli", "--punctuation-pause "),
                ("example", "0.15"),
                ("cli", "  --min-duration "),
                ("example", "1.00"),
                ("cli", "  --max-duration "),
                ("example", "6.00"),
            ),
            usage_note(
                "  ^ Optional timing knobs for slower, faster, denser, or more "
                "punctuated lyric lines."
            ),
            "",
            usage_command(
                ("cli", "--max-blank-end-marker-duration "),
                ("example", "12.0"),
                ("cli", "  --trust-blank-end-markers"),
            ),
            usage_note(
                "  ^ Control how blank LRC timestamps are treated as explicit "
                "end markers. By default, distant blank timestamps fall back "
                "to estimated lyric duration."
            ),
            "",
            usage_command(
                ("cli", "--gap-before-next "),
                ("example", "0.08"),
                ("cli", "  --merge-cues-within "),
                ("example", "0.35"),
            ),
            usage_note(
                "  ^ Keep a tiny gap before the next lyric and merge very "
                "nearby nonblank LRC lines into one cue."
            ),
            "",
            usage_command(("cli", "--song-length "), ("example", "4:12")),
            usage_note(
                "  ^ Cap estimated cue endings at a known song length. If this "
                "is omitted and the final lyric estimate needs a cap, the tool "
                "tries a same-named audio sidecar such as FLAC/MP3/WAV first; "
                f"a 200-file local survey needed this about {AUTO_AUDIO_DURATION_CAP_SURVEY_PERCENT}% "
                "of the time."
            ),
            "",
            usage_command(
                ("cli", "--line-width "),
                ("example", str(DEFAULT_LINE_WIDTH)),
                ("cli", "  --no-wrap"),
            ),
            usage_note(
                f"  ^ Default behavior wraps SRT text at {DEFAULT_LINE_WIDTH} "
                "characters per line. --line-width changes that width; "
                "--no-wrap disables wrapping and keeps each lyric line intact."
            ),
            "",
            usage_command(("cli", "--dry-run")),
            usage_note("  ^ Preview what would be converted or replaced without writing files."),
            "",
            usage_command(("cli", "-o  --output "), ("example", "song.srt")),
            usage_note(
                "  ^ Write one named input to a specific SRT path; not valid "
                "with wildcards, all/go, or regeneration modes."
            ),
            "",
            usage_command(("cli", "--self-test")),
            usage_note("  ^ Run the built-in unit tests, including smartquotes and audio probing checks."),
            "",
            usage_command(("cli", "-h  --help")),
            usage_note("  ^ Show argparse's plain help screen."),
            "",
            *usage_double_height_header(modes_header_text, ANSI_GREEN),
            "",
            usage_command(
                ("cli", "py lrc2srt.py --regenerate-converted-srts [--recursive] [--automatic-overwrites] [--dry-run]"),
            ),
            usage_note(
                "  ^ Rebuild only SRT files that this converter previously "
                "created, using the marker in the SRT and a "
                "same-named .lrc sidecar."
            ),
            "",
            usage_command(
                ("cli", "py lrc2srt.py --regenerate-all-srts [--recursive] [--automatic-overwrites] [--dry-run]"),
            ),
            usage_note(
                "  ^ Rebuild every matched SRT that has a same-named .lrc "
                "sidecar, even if the SRT was not originally made by this tool."
            ),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("special_mode", "all"),
                ("cli", " [--recursive] [--automatic-overwrites] [--dry-run]"),
            ),
            usage_note(
                "  ^ all means convert every *.lrc file in the current folder; "
                "add --recursive for subfolders and --automatic-overwrites for "
                "unattended batch replacement with backups."
            ),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("special_mode", "go"),
                ("cli", " [--recursive] [--automatic-overwrites] [--dry-run]"),
            ),
            usage_note(
                "  ^ go is the old quick shorthand for converting every "
                "*.lrc file in the current folder; use --recursive when you "
                "want subfolders too."
            ),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("special_mode", "MiniLyricsFix"),
                ("cli", " [--recursive] [--automatic-overwrites] [--dry-run]"),
            ),
            usage_note(
                "  ^ Generate SRT only if LRC & TXT both exist and SRT does "
                "not. Necessary to fix a MiniLyrics bug where timed subtitles "
                "are not displayed if there is an LRC and TXT present but not "
                "an SRT."
            ),
            "",
            *usage_double_height_header(examples_header_text, ANSI_GREEN),
            "",
            usage_command(("cli", "py lrc2srt.py "), ("example", "*.lrc")),
            usage_note("  ^ Convert every LRC in the current folder, prompting before replacements."),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("example", "*.lrc"),
                ("cli", " --recursive"),
            ),
            usage_note("  ^ Convert matching LRC files in this folder and every subfolder."),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("example", "*.lrc"),
                ("cli", " --automatic-overwrites"),
            ),
            usage_note("  ^ Batch-convert wildcard matches and back up existing SRTs without prompting."),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("special_mode", "all"),
                ("cli", " --recursive --automatic-overwrites"),
            ),
            usage_note("  ^ Convert all LRC files under this folder tree without stopping for prompts."),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("special_mode", "go"),
                ("cli", " --automatic-overwrites"),
            ),
            usage_note("  ^ Use the old go shorthand for the current folder and suppress overwrite prompts."),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("special_mode", "go"),
                ("cli", " --recursive --automatic-overwrites"),
            ),
            usage_note("  ^ Use go across the folder tree and suppress overwrite prompts."),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("special_mode", "MiniLyricsFix"),
                ("cli", " --recursive --automatic-overwrites"),
            ),
            usage_note("  ^ Fix missing MiniLyrics SRT sidecars throughout a folder tree."),
            "",
            usage_command(("cli", "py lrc2srt.py --regenerate-converted-srts --automatic-overwrites")),
            usage_note("  ^ Refresh only SRTs marked as created by this converter."),
            "",
            usage_command(("cli", "py lrc2srt.py --regenerate-converted-srts --recursive --automatic-overwrites")),
            usage_note("  ^ Refresh marked converter-made SRTs throughout the folder tree."),
            "",
            usage_command(("cli", "py lrc2srt.py --regenerate-all-srts --automatic-overwrites")),
            usage_note("  ^ Refresh every SRT in this folder that has a matching LRC sidecar."),
            "",
            usage_command(("cli", "py lrc2srt.py --regenerate-all-srts --recursive --automatic-overwrites")),
            usage_note("  ^ Refresh every SRT with a matching LRC sidecar throughout the folder tree."),
            "",
            usage_command(
                ("cli", "py lrc2srt.py "),
                ("example", '"Some Song.lrc"'),
                ("cli", " --seconds-per-word "),
                ("example", "0.65"),
            ),
            usage_note("  ^ Tune the duration estimate for a specific song with slower sung words."),
            "",
            *usage_double_height_header(logging_header_text, ANSI_GREEN),
            "",
            usage_note(
                f"  Every run appends JSON-lines records to {LOG_FILE}, "
                "including discovered tasks, folder changes, prompts, backups, "
                "writes, dry runs, skips, reviews, audio-duration probes, and "
                "self-tests."
            ),
            "",
        ]
    )


def console_safe_text(text: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        fallback_text = text.replace("\u2728", "*").replace("\u2731", "*")
        return fallback_text.encode(encoding, errors="replace").decode(
            encoding,
            errors="replace",
        )
    return text


def print_usage() -> None:
    print(console_safe_text(render_usage()))


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert LRC karaoke files to SRT subtitle files.",
        add_help=True,
    )
    parser.add_argument("input_files", nargs="*", help="Input LRC files or patterns")
    parser.add_argument("-a", "--all", action="store_true", help="Convert all .lrc files")
    parser.add_argument("-o", "--output", help="Output SRT file; only valid with one input")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Legacy alias for --automatic-overwrites",
    )
    parser.add_argument(
        "--automatic-overwrites",
        action="store_true",
        help="Back up and replace existing SRT files without overwrite/review prompts",
    )
    parser.add_argument(
        "--regenerate-converted-srts",
        action="store_true",
        help="Regenerate only SRT sidecars previously created by this converter",
    )
    parser.add_argument(
        "--regenerate-all-srts",
        action="store_true",
        help="Regenerate all SRT sidecars that have matching LRC files",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recurse through subfolders for wildcard/all/regeneration operations",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files")
    parser.add_argument("--seconds-per-word", type=float, default=DEFAULT_SECONDS_PER_WORD)
    parser.add_argument("--seconds-per-syllable", type=float, default=DEFAULT_SECONDS_PER_SYLLABLE)
    parser.add_argument("--line-padding", type=float, default=DEFAULT_LINE_PADDING_SECONDS)
    parser.add_argument("--punctuation-pause", type=float, default=DEFAULT_PUNCTUATION_PAUSE_SECONDS)
    parser.add_argument("--min-duration", type=float, default=DEFAULT_MIN_DURATION_SECONDS)
    parser.add_argument("--max-duration", type=float, default=DEFAULT_MAX_DURATION_SECONDS)
    parser.add_argument(
        "--max-blank-end-marker-duration",
        type=float,
        default=DEFAULT_MAX_BLANK_END_MARKER_DURATION_SECONDS,
        help=(
            "Longest blank LRC timestamp end marker to trust before falling "
            "back to estimated lyric duration"
        ),
    )
    parser.add_argument(
        "--trust-blank-end-markers",
        action="store_true",
        help="Trust blank LRC timestamp end markers no matter how far away they are",
    )
    parser.add_argument("--gap-before-next", type=float, default=DEFAULT_GAP_BEFORE_NEXT_LINE_SECONDS)
    parser.add_argument(
        "--merge-cues-within",
        type=float,
        default=DEFAULT_MERGE_CUES_WITHIN_SECONDS,
        help="Merge nonblank LRC lines whose starts are this many seconds apart",
    )
    parser.add_argument(
        "--line-width",
        type=int,
        default=DEFAULT_LINE_WIDTH,
        help=f"Wrap SRT text at this many characters; default {DEFAULT_LINE_WIDTH}",
    )
    parser.add_argument(
        "--no-wrap",
        action="store_true",
        help="Disable default SRT line wrapping and keep each lyric line intact",
    )
    parser.add_argument(
        "--song-length",
        help=(
            "Optional cap as seconds, MM:SS.xx, or HH:MM:SS.xx; when omitted, "
            "a same-named audio sidecar is probed only if the final lyric may need it"
        ),
    )
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests")
    return parser


def write_silent_wav_file(
    output_file: Path,
    duration_seconds: float,
    sample_rate: int = 8000,
) -> None:
    frame_count = int(round(duration_seconds * sample_rate))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_file), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\0\0" * frame_count)


def archive_self_test_directory(source_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    SELF_TEST_RECYCLED_ROOT.mkdir(parents=True, exist_ok=True)
    target = SELF_TEST_RECYCLED_ROOT / f"lrc2srt-self-test-{timestamp}"
    suffix = 1
    while target.exists():
        target = SELF_TEST_RECYCLED_ROOT / f"lrc2srt-self-test-{timestamp}-{suffix:03d}"
        suffix += 1
    return Path(shutil.move(str(source_dir), str(target)))


class Lrc2SrtUnitTests(unittest.TestCase):
    def predictable_options(self) -> ConversionOptions:
        return ConversionOptions(
            force=True,
            automatic_overwrites=True,
            seconds_per_word=0.50,
            seconds_per_syllable=0.00,
            line_padding_seconds=0.00,
            punctuation_pause_seconds=0.00,
            min_duration_seconds=1.00,
            max_duration_seconds=3.00,
            max_blank_end_marker_duration_seconds=12.00,
            gap_before_next_line_seconds=0.10,
            merge_cues_within_seconds=0.20,
            wrap_lines=False,
        )

    def assert_lrc_renders(self, lrc_text: str, expected_srt: str) -> None:
        actual_srt = lrc_text_to_srt(lrc_text.strip() + "\n", self.predictable_options())
        self.assertEqual(SRT_COMMENT_BLOCK + expected_srt.strip() + "\n", actual_srt)
        self.assertTrue(srt_text_was_created_by_this_tool(actual_srt))

    def test_unmarked_srt_is_not_detected_as_created_by_this_tool(self) -> None:
        self.assertFalse(
            srt_text_was_created_by_this_tool(
                "1\n00:00:01,000 --> 00:00:02,000\nplain subtitle\n"
            )
        )

    def test_render_usage_has_requested_order_and_explanations(self) -> None:
        usage = render_usage()
        plain_usage = re.sub(r"\033(?:\[[0-?]*[ -/]*[@-~]|#[0-9])", "", usage)
        title_header = "\u2728\u2731\u2728 lrc2srt \u2728\u2731\u2728"
        usage_header = "\u2728\u2731\u2728 Usage: \u2728\u2731\u2728"
        flags_header = "\u2728\u2731\u2728 Flags: \u2728\u2731\u2728"
        modes_header = "\u2728\u2731\u2728 Modes: \u2728\u2731\u2728"
        examples_header = "\u2728\u2731\u2728 Examples: \u2728\u2731\u2728"

        self.assertGreaterEqual(usage.count(ANSI_DOUBLE_HEIGHT_TOP), 6)
        self.assertGreaterEqual(usage.count(ANSI_DOUBLE_HEIGHT_BOTTOM), 6)
        self.assertIn(ANSI_CYAN, usage)
        self.assertIn(ANSI_BLUE, usage)
        self.assertIn(ANSI_DIM, usage)
        self.assertIn(ANSI_GREEN, usage)
        self.assertIn(ANSI_BLINK, usage)
        self.assertNotIn(ANSI_MAGENTA, usage)
        self.assertIn(f"{ANSI_BLINK}{ANSI_CYAN}all{ANSI_RESET}", usage)
        self.assertIn(f"{ANSI_BLINK}{ANSI_CYAN}go{ANSI_RESET}", usage)
        self.assertIn(f"{ANSI_BLINK}{ANSI_CYAN}MiniLyricsFix{ANSI_RESET}", usage)
        self.assertIn(title_header, usage)
        self.assertIn(usage_header, usage)
        self.assertIn(flags_header, usage)
        self.assertIn(modes_header, usage)
        self.assertIn(examples_header, usage)
        self.assertIn(
            "Conversion of timed lyric/subtitle files from LRC format to SRT format",
            plain_usage,
        )
        self.assertIn("end timestamps for each lyric", plain_usage)
        self.assertIn("^ Convert one or more named LRC files", plain_usage)
        self.assertIn(
            "^ Back up and replace existing SRT files without pausing",
            plain_usage,
        )
        self.assertIn("Include subfolders when expanding wildcards", plain_usage)
        self.assertIn("go, MiniLyricsFix, and regeneration modes", plain_usage)
        self.assertIn("print a folder header before that folder's files", plain_usage)
        self.assertIn("--seconds-per-word 0.65", plain_usage)
        self.assertIn("higher values keep lines onscreen longer", plain_usage)
        self.assertIn("--max-blank-end-marker-duration 12.0", plain_usage)
        self.assertIn("--trust-blank-end-markers", plain_usage)
        self.assertIn("--gap-before-next 0.08", plain_usage)
        self.assertIn("--merge-cues-within 0.35", plain_usage)
        self.assertIn("same-named audio sidecar", plain_usage)
        self.assertIn("200-file local survey needed this about 2%", plain_usage)
        self.assertIn("--self-test", plain_usage)
        self.assertIn("--help", plain_usage)
        self.assertIn("--dry-run", plain_usage)
        self.assertIn("^ all means convert every *.lrc file in the current folder", plain_usage)
        self.assertIn("^ go is the old quick shorthand", plain_usage)
        self.assertIn("Generate SRT only if LRC & TXT both exist and SRT does not", plain_usage)
        self.assertIn("MiniLyrics bug where timed subtitles are not displayed", plain_usage)
        self.assertIn("Rebuild only SRT files that this converter previously created", plain_usage)
        self.assertIn("Rebuild every matched SRT that has a same-named .lrc sidecar", plain_usage)
        self.assertIn(examples_header, plain_usage)
        self.assertIn("Tune the duration estimate for a specific song", plain_usage)

        commands_in_requested_order = [
            title_header,
            usage_header,
            "py lrc2srt.py song.lrc [more.lrc ...] [flags]",
            flags_header,
            "--automatic-overwrites",
            "--force",
            "--all",
            "--recursive",
            "--seconds-per-word 0.65",
            "--max-blank-end-marker-duration 12.0",
            "--gap-before-next 0.08",
            "--song-length 4:12",
            "--line-width 25",
            "--dry-run",
            "--output song.srt",
            "--self-test",
            "--help",
            modes_header,
            "py lrc2srt.py --regenerate-converted-srts [--recursive] [--automatic-overwrites] [--dry-run]",
            "py lrc2srt.py --regenerate-all-srts [--recursive] [--automatic-overwrites] [--dry-run]",
            "py lrc2srt.py all [--recursive] [--automatic-overwrites] [--dry-run]",
            "py lrc2srt.py go [--recursive] [--automatic-overwrites] [--dry-run]",
            "py lrc2srt.py MiniLyricsFix [--recursive] [--automatic-overwrites] [--dry-run]",
            examples_header,
            "py lrc2srt.py *.lrc",
        ]
        positions = [plain_usage.index(command) for command in commands_in_requested_order]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("py lrc2srt.py go --recursive --automatic-overwrites", plain_usage)
        self.assertIn("py lrc2srt.py MiniLyricsFix --recursive --automatic-overwrites", plain_usage)
        self.assertIn(f"--line-width {DEFAULT_LINE_WIDTH}", plain_usage)
        self.assertIn("Default behavior wraps SRT text at 25 characters", plain_usage)
        self.assertIn("Logging:", plain_usage)
        self.assertIn(str(LOG_FILE), plain_usage)
        parser_long_options = sorted(
            {
                option
                for action in build_argument_parser()._actions
                for option in action.option_strings
                if option.startswith("--")
            }
        )
        for option in parser_long_options:
            self.assertIn(option, plain_usage)

    def test_smart_quotes_are_preserved_and_dumb_quotes_are_smartened(self) -> None:
        self.assert_lrc_renders(
            """
[00:01.00]\u201cKeep\u201d "going" don't 'round `til \u00b4round \u00abalready\u00bb 5'6"
            """,
            """
1
00:00:01,000 --> 00:00:04,000
\u201cKeep\u201d \u201cgoing\u201d don\u2019t \u2019round \u2018til \u2019round \u00abalready\u00bb 5'6"
            """,
        )

    def test_explicit_blank_timestamp_becomes_end_marker(self) -> None:
        self.assert_lrc_renders(
            """
[ar:Example Artist]
[00:10.00]Hello world
[00:13.50]
            """,
            """
1
00:00:10,000 --> 00:00:13,500
Hello world
            """,
        )

    def test_distant_blank_timestamp_falls_back_to_estimate(self) -> None:
        self.assert_lrc_renders(
            """
[00:10.00]short line
[01:10.00]
            """,
            """
1
00:00:10,000 --> 00:00:11,000
short line
            """,
        )

    def test_too_close_blank_timestamp_falls_back_to_estimate(self) -> None:
        self.assert_lrc_renders(
            """
[00:00.00]Hello world
[00:00.01]
[00:10.00]Next line
            """,
            """
1
00:00:00,000 --> 00:00:01,000
Hello world

2
00:00:10,000 --> 00:00:11,000
Next line
            """,
        )

    def test_instrumental_gap_uses_estimated_duration_not_next_line(self) -> None:
        self.assert_lrc_renders(
            """
[00:30.00]One two
[00:50.00]After solo
            """,
            """
1
00:00:30,000 --> 00:00:31,000
One two

2
00:00:50,000 --> 00:00:51,000
After solo
            """,
        )

    def test_back_to_back_lines_trim_before_next_lyric(self) -> None:
        self.assert_lrc_renders(
            """
[00:01.00]one two three four
[00:02.00]next
            """,
            """
1
00:00:01,000 --> 00:00:01,900
one two three four

2
00:00:02,000 --> 00:00:03,000
next
            """,
        )

    def test_multiple_timestamps_on_one_line_expand_to_multiple_cues(self) -> None:
        self.assert_lrc_renders(
            """
[00:05.00][00:06.00]repeat me
            """,
            """
1
00:00:05,000 --> 00:00:05,900
repeat me

2
00:00:06,000 --> 00:00:07,000
repeat me
            """,
        )

    def test_nearby_lyric_timestamps_merge_to_avoid_flash_cues(self) -> None:
        self.assert_lrc_renders(
            """
[00:00.00]Title
[00:00.01]*
[00:02.00]First line
            """,
            """
1
00:00:00,000 --> 00:00:01,000
Title
*

2
00:00:02,000 --> 00:00:03,000
First line
            """,
        )

    def test_duplicate_same_timestamp_text_is_deduped(self) -> None:
        self.assert_lrc_renders(
            """
[00:08.00]same line
[00:08.00]same line
[00:10.00]new line
            """,
            """
1
00:00:08,000 --> 00:00:09,000
same line

2
00:00:10,000 --> 00:00:11,000
new line
            """,
        )

    def test_forced_replacement_creates_replaced_by_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_dir = Path(temporary_directory)
            lrc_file = temp_dir / "backup-test.lrc"
            srt_file = temp_dir / "backup-test.srt"
            lrc_file.write_text("[00:01.00]backup test\n", encoding="utf-8")
            srt_file.write_text("old subtitle\n", encoding="utf-8")

            result = convert_lrc_file(lrc_file, None, self.predictable_options())

            self.assertFalse(result.skipped)
            self.assertIsNotNone(result.backup_file)
            self.assertTrue(result.backup_file.exists())
            self.assertIn(".replaced-by-lrc2srt.bak", str(result.backup_file))
            self.assertTrue(srt_file.exists())
            self.assertTrue(srt_file_was_created_by_this_tool(srt_file))

    def test_minilyricsfix_mode_converts_only_lrc_txt_missing_srt(self) -> None:
        old_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_dir = Path(temporary_directory)
            eligible_lrc = temp_dir / "eligible.lrc"
            eligible_txt = temp_dir / "eligible.txt"
            missing_txt_lrc = temp_dir / "missing-txt.lrc"
            existing_srt_lrc = temp_dir / "existing-srt.lrc"
            existing_srt_txt = temp_dir / "existing-srt.txt"
            existing_srt = temp_dir / "existing-srt.srt"
            child_dir = temp_dir / "child"
            child_dir.mkdir()
            child_lrc = child_dir / "child-eligible.lrc"
            child_txt = child_dir / "child-eligible.txt"

            eligible_lrc.write_text("[00:01.00]eligible line\n", encoding="utf-8")
            eligible_txt.write_text("eligible line\n", encoding="utf-8")
            missing_txt_lrc.write_text("[00:01.00]missing txt\n", encoding="utf-8")
            existing_srt_lrc.write_text("[00:01.00]already has srt\n", encoding="utf-8")
            existing_srt_txt.write_text("already has srt\n", encoding="utf-8")
            existing_srt.write_text("do not replace\n", encoding="utf-8")
            child_lrc.write_text("[00:01.00]child line\n", encoding="utf-8")
            child_txt.write_text("child line\n", encoding="utf-8")

            try:
                os.chdir(temp_dir)
                exit_code = main(
                    [
                        "MiniLyricsFix",
                        "--recursive",
                        "--automatic-overwrites",
                    ]
                )
            finally:
                os.chdir(old_cwd)

            self.assertEqual(0, exit_code)
            self.assertTrue((temp_dir / "eligible.srt").exists())
            self.assertTrue((child_dir / "child-eligible.srt").exists())
            self.assertFalse((temp_dir / "missing-txt.srt").exists())
            self.assertEqual("do not replace\n", existing_srt.read_text(encoding="utf-8"))
            self.assertTrue(srt_file_was_created_by_this_tool(temp_dir / "eligible.srt"))

    def test_minilyricsfix_recursive_finds_child_when_root_has_no_lrc(self) -> None:
        old_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_dir = Path(temporary_directory) / "root [bracketed]"
            child_dir = temp_dir / "child"
            child_dir.mkdir(parents=True)
            child_lrc = child_dir / "child-only.lrc"
            child_txt = child_dir / "child-only.txt"
            child_srt = child_dir / "child-only.srt"
            child_lrc.write_text("[00:01.00]child only\n", encoding="utf-8")
            child_txt.write_text("child only\n", encoding="utf-8")

            try:
                os.chdir(temp_dir)
                exit_code = main(
                    [
                        "MiniLyricsFix",
                        "--recursive",
                        "--automatic-overwrites",
                    ]
                )
            finally:
                os.chdir(old_cwd)

            self.assertEqual(0, exit_code)
            self.assertTrue(child_srt.exists())
            self.assertTrue(srt_file_was_created_by_this_tool(child_srt))

    def test_main_output_uses_ansi_color_and_blank_line_before_summary(self) -> None:
        import contextlib
        import io

        old_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_dir = Path(temporary_directory)
            lrc_file = temp_dir / "color-test.lrc"
            lrc_file.write_text("[00:01.00]color output\n", encoding="utf-8")

            buffer = io.StringIO()
            try:
                os.chdir(temp_dir)
                with contextlib.redirect_stdout(buffer):
                    exit_code = main(["color-test.lrc", "--automatic-overwrites"])
            finally:
                os.chdir(old_cwd)

        output = buffer.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn(f"{ANSI_CYAN}    * Converting:", output)
        self.assertIn(f"{ANSI_BOLD}{ANSI_GREEN}       * Finished:", output)
        self.assertIn(f"\n\n{ANSI_BOLD}{ANSI_GREEN}* All done!", output)

    def test_audio_duration_probe_reads_wav_and_archives_fixture(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="lrc2srt-audio-probe-"))
        archived = False
        try:
            wav_file = temp_dir / "known-duration.wav"
            write_silent_wav_file(wav_file, 1.75)

            duration = probe_audio_duration_seconds(wav_file)

            self.assertIsNotNone(duration)
            self.assertAlmostEqual(1.75, duration or 0.0, delta=0.08)
            archived_path = archive_self_test_directory(temp_dir)
            archived = True
            self.assertEqual(SELF_TEST_RECYCLED_ROOT, archived_path.parent)
            self.assertRegex(archived_path.name, r"^lrc2srt-self-test-\d{14}")
            self.assertTrue((archived_path / "known-duration.wav").exists())
        except OSError as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            self.skipTest(f"Could not archive audio probe fixture to {SELF_TEST_RECYCLED_ROOT}: {exc}")
        finally:
            if not archived:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def test_audio_sidecar_caps_final_estimated_cue_when_needed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_dir = Path(temporary_directory)
            lrc_file = temp_dir / "audio-cap-test.lrc"
            wav_file = temp_dir / "audio-cap-test.wav"
            srt_file = temp_dir / "audio-cap-test.srt"
            lrc_file.write_text(
                "[00:01.00]one two three four five\n",
                encoding="utf-8",
            )
            write_silent_wav_file(wav_file, 2.50)
            options = ConversionOptions(
                force=True,
                automatic_overwrites=True,
                seconds_per_word=1.00,
                seconds_per_syllable=0.00,
                line_padding_seconds=1.00,
                punctuation_pause_seconds=0.00,
                min_duration_seconds=1.00,
                max_duration_seconds=8.00,
                max_blank_end_marker_duration_seconds=12.00,
                wrap_lines=False,
            )

            result = convert_lrc_file(lrc_file, None, options)

            self.assertFalse(result.skipped)
            self.assertTrue(srt_file.exists())
            self.assertIn(
                "00:00:01,000 --> 00:00:02,500",
                srt_file.read_text(encoding="utf-8"),
            )

    def test_default_wrap_width_is_25_and_no_wrap_disables_wrapping(self) -> None:
        self.assertEqual(25, DEFAULT_LINE_WIDTH)
        lrc_text = "[00:01.00]one two three four five six seven\n"
        wrapped_srt = lrc_text_to_srt(
            lrc_text,
            ConversionOptions(
                automatic_overwrites=True,
                seconds_per_word=0.10,
                seconds_per_syllable=0.00,
                line_padding_seconds=0.00,
                wrap_lines=True,
            ),
        )
        unwrapped_srt = lrc_text_to_srt(
            lrc_text,
            ConversionOptions(
                automatic_overwrites=True,
                seconds_per_word=0.10,
                seconds_per_syllable=0.00,
                line_padding_seconds=0.00,
                wrap_lines=False,
            ),
        )

        self.assertIn("one two three four five\nsix seven", wrapped_srt)
        self.assertIn("one two three four five six seven", unwrapped_srt)


def run_self_test() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Lrc2SrtUnitTests)
    suite.addTests(smartquotes.load_unit_tests())
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise AssertionError("Self-test failed.")
    print_success("Self-test passed.")


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    raw_argv = ["--all" if argument.lower() == "-all" else argument for argument in raw_argv]

    if not raw_argv:
        print_usage()
        return 1

    parser = build_argument_parser()
    args = parser.parse_args(raw_argv)

    log_event(
        "tool_started",
        argv=raw_argv,
        cwd=str(Path.cwd()),
    )

    if args.self_test:
        log_event("self_test_started")
        run_self_test()
        log_event("self_test_completed")
        return 0

    patterns: list[str] = []
    process_all = args.all
    process_minilyricsfix = False
    force = args.force

    for item in args.input_files:
        lowered = item.lower()
        if lowered == "force":
            force = True
        elif lowered == "minilyricsfix":
            process_minilyricsfix = True
        elif lowered in {"go", "all", "*", "*.lrc"}:
            if args.regenerate_all_srts or args.regenerate_converted_srts:
                patterns.append("*.srt")
            else:
                process_all = True
        else:
            patterns.append(item)

    if args.regenerate_all_srts and args.regenerate_converted_srts:
        print_error("Error: choose only one regeneration mode.")
        log_event("tool_error", error="both_regeneration_modes_requested")
        return 1

    if process_minilyricsfix and (args.regenerate_all_srts or args.regenerate_converted_srts):
        print_error("Error: Cannot combine MiniLyricsFix with regeneration modes.")
        log_event("tool_error", error="minilyricsfix_with_regeneration")
        return 1

    if (
        not process_all
        and not process_minilyricsfix
        and not patterns
        and not args.regenerate_all_srts
        and not args.regenerate_converted_srts
    ):
        print_usage()
        return 1

    automatic_overwrites = args.automatic_overwrites or force

    if (args.regenerate_all_srts or args.regenerate_converted_srts) and args.output:
        print_error("Error: Cannot specify --output with regeneration modes.")
        log_event("tool_error", error="output_with_regeneration")
        return 1

    if process_minilyricsfix and args.output:
        print_error("Error: Cannot specify --output with MiniLyricsFix mode.")
        log_event("tool_error", error="output_with_minilyricsfix")
        return 1

    options = ConversionOptions(
        force=force,
        automatic_overwrites=automatic_overwrites,
        dry_run=args.dry_run,
        seconds_per_word=args.seconds_per_word,
        seconds_per_syllable=args.seconds_per_syllable,
        line_padding_seconds=args.line_padding,
        punctuation_pause_seconds=args.punctuation_pause,
        min_duration_seconds=args.min_duration,
        max_duration_seconds=args.max_duration,
        max_blank_end_marker_duration_seconds=(
            None
            if args.trust_blank_end_markers
            else args.max_blank_end_marker_duration
        ),
        gap_before_next_line_seconds=args.gap_before_next,
        merge_cues_within_seconds=args.merge_cues_within,
        line_width=args.line_width,
        wrap_lines=not args.no_wrap,
        song_length_seconds=(
            parse_duration_or_timestamp(args.song_length)
            if args.song_length
            else None
        ),
    )
    validate_options(options)

    try:
        if args.regenerate_converted_srts:
            print()
            print_info("* Regenerating SRT files previously created by this converter...")
            tasks = build_regeneration_tasks(
                patterns,
                args.recursive,
                converted_only=True,
            )
        elif args.regenerate_all_srts:
            print()
            print_info("* Regenerating all SRT files with matching LRC sidecars...")
            tasks = build_regeneration_tasks(
                patterns,
                args.recursive,
                converted_only=False,
            )
        elif process_minilyricsfix:
            print()
            print_info(
                "* MiniLyricsFix: generating SRT only where LRC and TXT exist "
                "but SRT is missing..."
            )
            tasks = build_minilyricsfix_tasks(
                patterns,
                args.recursive,
            )
        else:
            print()
            print_info("* About to convert LRC files to SRT...")
            tasks = build_lrc_tasks(
                patterns,
                process_all,
                args.recursive,
                args.output,
            )
    except ValueError as exc:
        print_error(f"Error: {exc}")
        log_event("tool_error", error=str(exc))
        return 1

    if not tasks:
        print_warning("No files to process.")
        log_event("tool_finished", tasks=0, converted=0, skipped=0)
        return 1

    unique_parent_count = len({str(task.input_file.parent.resolve()) for task in tasks})
    show_folder_headers = args.recursive or unique_parent_count > 1

    log_event(
        "tasks_discovered",
        task_count=len(tasks),
        recursive=args.recursive,
        regenerate_converted_srts=args.regenerate_converted_srts,
        regenerate_all_srts=args.regenerate_all_srts,
        minilyricsfix=process_minilyricsfix,
        automatic_overwrites=automatic_overwrites,
    )

    results = run_conversion_tasks(tasks, options, show_folder_headers)
    converted_count = len([result for result in results if not result.skipped])
    skipped_count = len([result for result in results if result.skipped])

    print()
    print_success(
        f"* All done! Converted/regenerated: {converted_count}; "
        f"skipped: {skipped_count}; log: {LOG_FILE}"
    )
    log_event(
        "tool_finished",
        tasks=len(tasks),
        converted=converted_count,
        skipped=skipped_count,
        log_file=str(LOG_FILE),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
