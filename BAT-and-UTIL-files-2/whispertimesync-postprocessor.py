#!/usr/bin/env python3

"""
whispertimesync-postprocessor

Clone any missing subtitle coverage from an older SRT into a newer SRT when the newer file starts later,
ends earlier, or both.

Behavior:
- Reads OLD_SRT and NEW_SRT defensively, including legacy encodings when possible.
- Parses both SRTs, reports each file's first and last subtitle timestamps, and compares them.
- If NEW_SRT starts later than OLD_SRT, prepends OLD_SRT cues from before that cutoff into NEW_SRT.
- If NEW_SRT ends earlier than OLD_SRT, appends OLD_SRT cues from after that cutoff into NEW_SRT.
- If both are true, does both in one pass.
- Before overwriting NEW_SRT, creates a backup beside it named like: original.srt.YYYYMMDDHHMMSS.bak
- Never crashes on ordinary bad input; errors are caught and reported.

Notes:
- "Timestamp" here means subtitle timestamps inside the SRT, not filesystem modified time.
- Cue numbers are renumbered on output for a clean final SRT.
- Boundary logic tries to preserve overlapping donor cues when they truly extend beyond NEW_SRT's coverage,
  but skips them when they are effectively duplicates of cues already present in NEW_SRT.
"""

from __future__ import annotations  # allow modern type hint syntax consistently
import argparse, ctypes, os, re, sys, traceback, shutil  # standard libs used by this script
from dataclasses import dataclass  # simple structured cue container
from datetime import datetime  # for YYYYMMDDHHMMSS backup timestamps
from pathlib import Path  # safer path handling than raw strings
from typing import Iterable  # used for typed iterable function input

APP_NAME = "whispertimesync-postprocessor"  # program name shown in usage/help
RESET = "\033[0m"  # ANSI reset code to end color formatting
COLORS = {
    "very_important": "\033[96;1m",  # bright cyan
    "important": "\033[36m",         # cyan
    "warning": "\033[37;44;1m",      # white on blue
    "soft_warning": "\033[33m",      # yellow
    "advice": "\033[35m",            # purple/magenta
    "less_important": "\033[90m",    # dim gray
    "success": "\033[32m",           # green
    "error": "\033[97;41;1m",        # white on red
}
ICONS = {
    "very_important": "✨" ,   # visually strong FYI / big notice
    "important"     : "⛧"  ,   # normal informative output
    "less_important": "⭐"  ,   # lower-priority informational output
    "warning"       : "⚠️" ,   # higher-attention warning
    "soft_warning"  : "❕"   ,   # softer warning
    "advice"        : "➜"  ,   # advice/tip style output
    "success"       : "✅" ,   # success output
    "error"         : "🛑" ,   # hard error output
}

@dataclass
class Cue:
    index: int      # original cue number, though final rendering renumbers cleanly
    start_ms: int   # cue start time in milliseconds
    end_ms: int     # cue end time in milliseconds
    text: str       # cue subtitle text body

def enable_utf8_stdio() -> None:
    for stream_name in ("stdin", "stdout", "stderr"):  # update all standard streams
        stream = getattr(sys, stream_name, None)  # fetch the stream object safely
        if hasattr(stream, "reconfigure"):  # only works on streams that support reconfigure()
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")  # allow emoji/unicode safely
            except Exception:
                pass  # do not fail just because reconfigure is unavailable/broken

def enable_windows_ansi() -> None:
    if os.name != "nt":  # only needed on Windows consoles
        return
    try:
        kernel32 = ctypes.windll.kernel32  # access Win32 console API
        handle = kernel32.GetStdHandle(-11)  # -11 = STD_OUTPUT_HANDLE
        if handle in (0, -1):  # invalid console handle, bail quietly
            return
        mode = ctypes.c_uint()  # storage for current console mode flags
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):  # read current mode
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # enable virtual terminal / ANSI output
    except Exception:
        pass  # if ANSI enabling fails, script still works with plain text

def paint(level: str, text: str) -> str:
    return f"{COLORS.get(level, '')}{text}{RESET}"  # wrap a string in ANSI color + reset

def say(level: str, message: str) -> None:
    icon = ICONS.get(level, "• ")  # choose emoji/icon for this message level
    print(f"{paint(level, icon)} {paint(level, message)}")  # print icon + space + colored message

def format_ms(ms: int) -> str:
    ms = max(0, int(ms))  # ensure non-negative integer milliseconds
    h, rem = divmod(ms, 3_600_000)  # split hours from remainder
    m, rem = divmod(rem, 60_000)    # split minutes from remainder
    s, ms = divmod(rem, 1_000)      # split seconds from remaining milliseconds
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"  # standard SRT timestamp format

_TS_RE = re.compile(
    r"^\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*"  # left/start timestamp
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})(?:\s+.*)?$",   # right/end timestamp, allowing trailing style info
    re.MULTILINE,  # allow matching a timestamp line within a block
)

def ts_to_ms(h: str, m: str, s: str, ms: str) -> int:
    return ((int(h) * 3600 + int(m) * 60 + int(s)) * 1000) + int(ms.ljust(3, "0")[:3])  # normalize to 3-digit ms

def normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")  # normalize BOM/newlines
    text = "\n".join(line.rstrip() for line in text.split("\n"))  # strip trailing whitespace per line
    return text.strip()  # strip leading/trailing empty space overall

def split_blocks(text: str) -> list[str]:
    text = normalize_text(text)  # normalize before splitting into subtitle blocks
    return [block.strip("\n") for block in re.split(r"\n\s*\n", text) if block.strip()]  # split on blank lines

def parse_srt(text: str) -> list[Cue]:
    cues: list[Cue] = []  # parsed cues will accumulate here
    for block in split_blocks(text):  # process each subtitle block separately
        lines = [line.rstrip("\n") for line in block.split("\n")]  # split block into lines cleanly
        if not lines:
            continue  # skip impossible/empty blocks just in case
        ts_line_idx = 1 if len(lines) >= 2 and lines[0].strip().isdigit() and "-->" in lines[1] else 0  # allow numbered and unnumbered blocks
        if ts_line_idx >= len(lines):
            continue  # defensive skip if malformed
        match = _TS_RE.match(lines[ts_line_idx].strip())  # parse timestamp line
        if not match:
            continue  # skip blocks with no valid SRT timing line
        start_ms = ts_to_ms(*match.groups()[:4])  # convert start timestamp to milliseconds
        end_ms = ts_to_ms(*match.groups()[4:8])   # convert end timestamp to milliseconds
        if end_ms < start_ms:
            start_ms, end_ms = end_ms, start_ms  # repair reversed timestamps instead of crashing
        text_lines = lines[ts_line_idx + 1:] if ts_line_idx + 1 < len(lines) else [""]  # everything after timing is subtitle text
        cues.append(Cue(index=len(cues) + 1, start_ms=start_ms, end_ms=end_ms, text="\n".join(text_lines).strip()))  # store cue
    return cues  # return fully parsed cue list

def render_srt(cues: Iterable[Cue]) -> str:
    out: list[str] = []  # collect output lines efficiently
    for i, cue in enumerate(cues, 1):  # renumber cues from 1 regardless of old numbering
        out.extend([str(i), f"{format_ms(cue.start_ms)} --> {format_ms(cue.end_ms)}", cue.text, ""])  # one SRT block
    return "\r\n".join(out).rstrip() + "\r\n"  # Windows-friendly line endings, trailing newline

def detect_encoding(raw: bytes, sample_size: int = 131072) -> str:
    sample = raw[:sample_size]  # inspect just the first chunk; usually enough for detection
    if sample.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"  # UTF-8 BOM
    if sample.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le"  # UTF-32 little-endian BOM
    if sample.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be"  # UTF-32 big-endian BOM
    if sample.startswith(b"\xff\xfe"):
        return "utf-16-le"  # UTF-16 little-endian BOM
    if sample.startswith(b"\xfe\xff"):
        return "utf-16-be"  # UTF-16 big-endian BOM
    try:
        from charset_normalizer import from_bytes  # preferred library if installed
        best = from_bytes(sample).best()  # ask library for best guess
        if best and getattr(best, "encoding", None):
            return best.encoding  # return detected encoding if available
    except Exception:
        pass  # silently continue to next method
    try:
        import chardet  # fallback detection library if installed
        guess = chardet.detect(sample)  # ask chardet for a guess
        if guess and guess.get("encoding"):
            return guess["encoding"]  # use guessed encoding if present
    except Exception:
        pass  # silently continue to manual fallbacks
    for enc in ("utf-8", "utf-16", "cp1252", "latin-1"):  # try a few common encodings directly
        try:
            sample.decode(enc)  # if decode works, treat that as acceptable
            return enc
        except Exception:
            continue
    return "latin-1"  # last-resort encoding that never really fails to decode bytes

def read_text_file(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()  # read the file as raw bytes first so we can control decoding
    enc = detect_encoding(raw)  # guess encoding from BOM / detector / fallbacks
    try:
        return raw.decode(enc), enc  # try decoding with the detected encoding
    except Exception:
        for fallback in ("utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1"):  # alternate decoders
            try:
                return raw.decode(fallback), fallback  # return first successful decode
            except Exception:
                continue
    return raw.decode("utf-8", errors="replace"), "utf-8(replace)"  # never crash: replace bad chars if necessary

def cues_sameish(a: Cue, b: Cue) -> bool:
    ta = " ".join(normalize_text(a.text).split())  # normalize whitespace/text of cue A
    tb = " ".join(normalize_text(b.text).split())  # normalize whitespace/text of cue B
    return ta == tb and abs(a.start_ms - b.start_ms) <= 150 and abs(a.end_ms - b.end_ms) <= 150  # near-identical timing + text

def choose_head(OLD_SRT: list[Cue], NEW_SRT: list[Cue]) -> tuple[list[Cue], bool]:
    if not OLD_SRT:
        return [], False  # no old cues means there is nothing available to prepend
    if not NEW_SRT:
        return [], False  # the completely-empty NEW_SRT case is handled separately in run()

    new_start_ms = NEW_SRT[0].start_ms  # starting timestamp of the first cue already present in NEW_SRT

    boundary = next((i for i, cue in enumerate(OLD_SRT) if cue.start_ms >= new_start_ms), None)  # first old cue that starts at/after NEW_SRT's first cue
    head = list(OLD_SRT if boundary is None else OLD_SRT[:boundary])  # everything before that boundary is candidate "head" material

    overlap_included = bool(head and head[-1].start_ms < new_start_ms < head[-1].end_ms)  # note whether the last prepended cue overlaps into NEW_SRT's first cue
    if head and cues_sameish(head[-1], NEW_SRT[0]):
        head = head[:-1]  # drop the last prepended cue if it is effectively already present as NEW_SRT's first cue
        overlap_included = False  # if we dropped it, there is no overlap worth reporting anymore

    return head, overlap_included  # return prepended cues plus whether a boundary-overlap cue was intentionally kept

def choose_tail(OLD_SRT: list[Cue], NEW_SRT: list[Cue]) -> tuple[list[Cue], bool]:
    if not OLD_SRT:
        return [], False  # no old cues means nothing to append
    if not NEW_SRT:
        return list(OLD_SRT), False  # empty new file gets the entire old subtitle list
    new_end_ms = NEW_SRT[-1].end_ms  # end timestamp of the last new cue
    boundary = next((i for i, cue in enumerate(OLD_SRT) if cue.end_ms > new_end_ms), None)  # first old cue that extends beyond the new end
    if boundary is None:
        return [], False  # old file does not extend past new file, so no tail exists
    tail = list(OLD_SRT[boundary:])  # collect the old cues from that boundary onward
    overlap_included = bool(tail and tail[0].start_ms < new_end_ms < tail[0].end_ms)  # note if first appended cue overlaps the cutoff
    if tail and cues_sameish(NEW_SRT[-1], tail[0]):
        tail = tail[1:]  # if boundary cue is basically already present, skip duplicate
        overlap_included = False  # if skipped, we no longer have overlap to mention
    return tail, overlap_included  # return chosen tail and overlap note flag

def make_backup_path(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # build YYYYMMDDHHMMSS timestamp
    return path.with_name(f"{path.name}.{timestamp}.bak")  # create backup filename in same folder

def print_usage_old(parser: argparse.ArgumentParser) -> None:
    say("very_important", f"{APP_NAME} clones the missing subtitle tail from OLD_SRT into NEW_SRT when needed.")  # top summary
    print()  # blank line for readability
    say("important", "Usage:")  # usage label
    print(paint("important", f"  {APP_NAME} OLD_SRT NEW_SRT"))  # actual usage line
    print()  # blank line
    say("advice", "Example:")  # example label
    print(paint("advice", f"  {APP_NAME} old.srt new.srt"))  # actual example command
    print()  # blank line
    say("less_important", "If NEW_SRT ends earlier than OLD_SRT, NEW_SRT is backed up and then overwritten in place.")  # explain overwrite behavior
    say("less_important", "If NEW_SRT already reaches at least as far as OLD_SRT, nothing is overwritten.")  # explain no-op behavior
    print()  # blank line
    parser.print_help()  # argparse-generated help text

def print_usage(parser: argparse.ArgumentParser) -> None:
    say("very_important", f"{APP_NAME} clones missing subtitle coverage from OLD_SRT into NEW_SRT when needed.")  # top summary
    print()  # blank line for readability
    say("important", "Usage:")  # usage label
    print(paint("important", f"  {APP_NAME} OLD_SRT NEW_SRT"))  # actual usage line
    print()  # blank line
    say("advice", "Example:")  # example label
    print(paint("advice", f"  {APP_NAME} old.srt new.srt"))  # actual example command
    print()  # blank line
    say("less_important", "If NEW_SRT starts later than OLD_SRT, missing earlier cues are prepended into NEW_SRT.")  # explain head-cloning behavior
    say("less_important", "If NEW_SRT ends earlier than OLD_SRT, missing later cues are appended into NEW_SRT.")  # explain tail-cloning behavior
    say("less_important", "If either change is needed, NEW_SRT is backed up and then overwritten in place.")  # explain overwrite behavior
    say("less_important", "If NEW_SRT already covers the same or wider time range, nothing is overwritten.")  # explain no-op behavior
    print()  # blank line
    parser.print_help()  # argparse-generated help text

def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=True, prog=APP_NAME, description="Clone missing beginning/end subtitle coverage from OLD_SRT into NEW_SRT.")  # build parser
    parser.add_argument("OLD_SRT", nargs="?", help="older/reference SRT file")  # first positional argument
    parser.add_argument("NEW_SRT", nargs="?", help="newer/current SRT file that may be missing early and/or late coverage")  # second positional argument
    return parser  # return configured parser

def make_parser_old() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=True, prog=APP_NAME, description="Clone missing subtitle tail from OLD_SRT into NEW_SRT.")  # build parser
    parser.add_argument("OLD_SRT", nargs="?", help="older/reference SRT file")  # first positional argument
    parser.add_argument("NEW_SRT", nargs="?", help="newer/current SRT file that may end too early")  # second positional argument
    return parser  # return configured parser

def run(argv: list[str]) -> int:
    enable_utf8_stdio()  # make stdin/stdout/stderr more Unicode-safe
    enable_windows_ansi()  # turn on ANSI colors in Windows console if possible
    parser = make_parser()  # construct CLI parser

    if len(argv) == 1:
        print_usage(parser)  # no arguments: show usage/help
        return 0  # normal exit

    args = parser.parse_args(argv[1:])  # parse command line after script name
    if not args.OLD_SRT or not args.NEW_SRT:
        say("warning", "You must provide both OLD_SRT and NEW_SRT.")  # missing required positional args
        print()  # blank line
        print_usage(parser)  # show usage again
        return 2  # conventional CLI usage error

    old_path = Path(args.OLD_SRT)  # convert OLD_SRT path string to Path object
    new_path = Path(args.NEW_SRT)  # convert NEW_SRT path string to Path object

    try:
        if not old_path.exists():
            say("error", f"OLD_SRT not found: {old_path}")  # fail if old file does not exist
            return 2
        if not new_path.exists():
            say("error", f"NEW_SRT not found: {new_path}")  # fail if new file does not exist
            return 2
        if old_path.is_dir() or new_path.is_dir():
            say("error", "OLD_SRT and NEW_SRT must be files, not directories.")  # directories are not valid input
            return 2

        say("important", f"Reading OLD_SRT: {old_path}")  # tell user what is being read
        old_text, old_enc = read_text_file(old_path)  # read old file with defensive decoding
        say("important", f"Reading NEW_SRT: {new_path}")  # tell user what is being read
        new_text, new_enc = read_text_file(new_path)  # read new file with defensive decoding
        say("less_important", f"Detected encodings: OLD_SRT={old_enc} | NEW_SRT={new_enc}")  # FYI only

        OLD_SRT = parse_srt(old_text)  # required variable name: parsed old cues
        NEW_SRT = parse_srt(new_text)  # required variable name: parsed new cues

        if not OLD_SRT:
            say("soft_warning", "OLD_SRT did not yield any parseable subtitle cues.")  # old file parsed to nothing
        if not NEW_SRT:
            say("soft_warning", "NEW_SRT did not yield any parseable subtitle cues.")  # new file parsed to nothing

        old_first_ms = OLD_SRT[0].start_ms if OLD_SRT else 0  # first old cue start time or 0 if empty
        old_last_ms = OLD_SRT[-1].end_ms if OLD_SRT else 0  # last old cue end time or 0 if empty
        new_first_ms = NEW_SRT[0].start_ms if NEW_SRT else 0  # first new cue start time or 0 if empty
        new_last_ms = NEW_SRT[-1].end_ms if NEW_SRT else 0  # last new cue end time or 0 if empty

        say("very_important", f"OLD_SRT first subtitle timestamp: {format_ms(old_first_ms)}")  # beginning-of-file FYI
        say("very_important", f"OLD_SRT last subtitle timestamp:  {format_ms(old_last_ms)}")  # end-of-file FYI
        say("very_important", f"NEW_SRT first subtitle timestamp: {format_ms(new_first_ms)}")  # beginning-of-file FYI
        say("very_important", f"NEW_SRT last subtitle timestamp:  {format_ms(new_last_ms)}")  # end-of-file FYI

        prepended = False  # track whether we actually prepended any head cues
        prepended_count = 0  # track how many cues were prepended
        appended = False  # track whether we actually appended any tail cues
        appended_count = 0  # track how many cues were appended
        head_overlap_included = False  # track whether a prepended boundary-overlap cue was intentionally kept
        tail_overlap_included = False  # track whether an appended boundary-overlap cue was intentionally kept
        final_cues = list(NEW_SRT)  # begin with the currently parsed NEW_SRT as the starting output

        if OLD_SRT and not NEW_SRT:
            final_cues = [Cue(index=0, start_ms=c.start_ms, end_ms=c.end_ms, text=c.text) for c in OLD_SRT]  # if NEW_SRT is empty/unparseable, copy all old cues into it
            prepended = True  # reuse "prepended" flag to indicate that NEW_SRT gained earlier coverage
            prepended_count = len(final_cues)  # report how many cues were copied
        else:
            if OLD_SRT and NEW_SRT and new_first_ms > old_first_ms:
                head, head_overlap_included = choose_head(OLD_SRT, NEW_SRT)  # collect any older cues that belong before NEW_SRT starts
                if head:
                    final_cues = [Cue(index=0, start_ms=c.start_ms, end_ms=c.end_ms, text=c.text) for c in head] + final_cues  # prepend copied head cues
                    prepended = True  # record that a prepend occurred
                    prepended_count = len(head)  # record number of prepended cues

            if OLD_SRT and NEW_SRT and new_last_ms < old_last_ms:
                tail, tail_overlap_included = choose_tail(OLD_SRT, NEW_SRT)  # collect any later cues that belong after NEW_SRT ends
                if tail:
                    final_cues.extend(Cue(index=0, start_ms=c.start_ms, end_ms=c.end_ms, text=c.text) for c in tail)  # append copied tail cues
                    appended = True  # record that an append occurred
                    appended_count = len(tail)  # record number of appended cues

        changed = prepended or appended  # only back up and overwrite if we actually changed NEW_SRT

        if changed:
            backup_path = make_backup_path(new_path)  # compute backup filename before touching NEW_SRT
            shutil.copy2(new_path, backup_path)  # preserve original NEW_SRT with metadata/timestamps if possible
            new_path.write_text(render_srt(final_cues), encoding="utf-8-sig", newline="")  # overwrite NEW_SRT in UTF-8 BOM form

            if not NEW_SRT and OLD_SRT:
                say("success", f"NEW_SRT had no parseable cues, so copied {prepended_count} cue(s) from OLD_SRT into it.")  # special-case success message for empty NEW_SRT
            else:
                if prepended:
                    say("success", f"Prepended {prepended_count} cue(s) from OLD_SRT so NEW_SRT reaches the old beginning.")  # head-clone success message
                if appended:
                    say("success", f"Appended {appended_count} cue(s) from OLD_SRT so NEW_SRT reaches the old ending.")  # tail-clone success message

            say("less_important", f"Backed up overwritten NEW_SRT to: {backup_path}")  # backup FYI
            say("less_important", f"Overwrote NEW_SRT in place: {new_path}")  # overwrite FYI

            if head_overlap_included:
                say("soft_warning", "The last prepended cue overlaps NEW_SRT's beginning, so it was kept to preserve the head.")  # boundary-case FYI for prepending
            if tail_overlap_included:
                say("soft_warning", "The first appended cue overlaps NEW_SRT's ending, so it was kept to preserve the tail.")  # boundary-case FYI for appending
        else:
            say("less_important", "No prepend or append needed: NEW_SRT already covers the same or wider time range.")  # normal no-op case
            say("less_important", "No file was overwritten.")  # explicitly state no overwrite happened

        say("less_important", f"Prepend performed: {'yes' if prepended else 'no'}")  # low-priority prepend result
        if prepended:
            say("less_important", f"Number of prepended cues: {prepended_count}")  # extra detail if prepend occurred

        say("less_important", f"Append performed: {'yes' if appended else 'no'}")  # low-priority append result
        if appended:
            say("less_important", f"Number of appended cues: {appended_count}")  # extra detail if append occurred

        say("advice", "Files written by this script use UTF-8 with BOM for broad subtitle-editor compatibility.")  # final tip
        return 0  # success exit code

    except KeyboardInterrupt:
        say("warning", "Interrupted by user.")  # graceful Ctrl+C handling
        return 130  # conventional interrupted-process exit code
    except Exception as exc:
        say("error", f"Unexpected error: {exc}")  # catch-all failure message
        tb = traceback.format_exc().strip().splitlines()  # get traceback lines for compact reporting
        say("less_important", tb[-1] if tb else "No traceback available.")  # show last traceback line as FYI
        return 1  # generic failure exit code

def run_old(argv: list[str]) -> int:
    enable_utf8_stdio()  # make stdin/stdout/stderr more Unicode-safe
    enable_windows_ansi()  # turn on ANSI colors in Windows console if possible
    parser = make_parser()  # construct CLI parser

    if len(argv) == 1:
        print_usage(parser)  # no arguments: show usage/help
        return 0  # normal exit

    args = parser.parse_args(argv[1:])  # parse command line after script name
    if not args.OLD_SRT or not args.NEW_SRT:
        say("warning", "You must provide both OLD_SRT and NEW_SRT.")  # missing required positional args
        print()  # blank line
        print_usage(parser)  # show usage again
        return 2  # conventional CLI usage error

    old_path = Path(args.OLD_SRT)  # convert OLD_SRT path string to Path object
    new_path = Path(args.NEW_SRT)  # convert NEW_SRT path string to Path object

    try:
        if not old_path.exists():
            say("error", f"OLD_SRT not found: {old_path}")  # fail if old file does not exist
            return 2
        if not new_path.exists():
            say("error", f"NEW_SRT not found: {new_path}")  # fail if new file does not exist
            return 2
        if old_path.is_dir() or new_path.is_dir():
            say("error", "OLD_SRT and NEW_SRT must be files, not directories.")  # directories are not valid input
            return 2

        say("important", f"Reading OLD_SRT: {old_path}")  # tell user what is being read
        old_text, old_enc = read_text_file(old_path)  # read old file with defensive decoding
        say("important", f"Reading NEW_SRT: {new_path}")  # tell user what is being read
        new_text, new_enc = read_text_file(new_path)  # read new file with defensive decoding
        say("less_important", f"Detected encodings: OLD_SRT={old_enc} | NEW_SRT={new_enc}")  # FYI only

        OLD_SRT = parse_srt(old_text)  # required variable name: parsed old cues
        NEW_SRT = parse_srt(new_text)  # required variable name: parsed new cues

        if not OLD_SRT:
            say("soft_warning", "OLD_SRT did not yield any parseable subtitle cues.")  # old file parsed to nothing
        if not NEW_SRT:
            say("soft_warning", "NEW_SRT did not yield any parseable subtitle cues.")  # new file parsed to nothing

        old_last_ms = OLD_SRT[-1].end_ms if OLD_SRT else 0  # last old cue end time or 0 if empty
        new_last_ms = NEW_SRT[-1].end_ms if NEW_SRT else 0  # last new cue end time or 0 if empty
        say("very_important", f"OLD_SRT last subtitle timestamp: {format_ms(old_last_ms)}")  # requested FYI display
        say("very_important", f"NEW_SRT last subtitle timestamp: {format_ms(new_last_ms)}")  # requested FYI display

        appended = False  # track whether we actually appended any tail
        appended_count = 0  # track how many cues were appended
        final_cues = list(NEW_SRT)  # start final output from existing new cues

        if new_last_ms < old_last_ms:
            tail, overlap_included = choose_tail(OLD_SRT, NEW_SRT)  # choose the portion of old subtitles to append
            if tail:
                final_cues.extend(Cue(index=0, start_ms=c.start_ms, end_ms=c.end_ms, text=c.text) for c in tail)  # append copied cues
                backup_path = make_backup_path(new_path)  # compute backup filename before overwriting
                shutil.copy2(new_path, backup_path)  # preserve original NEW_SRT with metadata/timestamps if possible
                new_path.write_text(render_srt(final_cues), encoding="utf-8-sig", newline="")  # overwrite NEW_SRT in UTF-8 BOM
                appended = True  # record that append happened
                appended_count = len(tail)  # record number of appended cues
                say("success", f"Appended {appended_count} cue(s) from OLD_SRT so NEW_SRT reaches the old ending.")  # success message
                say("less_important", f"Backed up overwritten NEW_SRT to: {backup_path}")  # backup FYI
                say("less_important", f"Overwrote NEW_SRT in place: {new_path}")  # overwrite FYI
                if overlap_included:
                    say("soft_warning", "The first appended cue overlaps NEW_SRT's ending, so it was kept to preserve the tail.")  # boundary-case FYI
            else:
                say("soft_warning", "NEW_SRT ends earlier, but no safe tail cues were found to append.")  # no safe append despite shorter end
        else:
            say("less_important", "No append needed: NEW_SRT already ends at or after OLD_SRT.")  # normal no-op case
            say("less_important", "No file was overwritten.")  # explicitly state no overwrite happened

        say("less_important", f"Append performed: {'yes' if appended else 'no'}")  # requested low-priority append result
        if appended:
            say("less_important", f"Number of appended cues: {appended_count}")  # extra detail if append occurred
        say("advice", "Files written by this script use UTF-8 with BOM for broad subtitle-editor compatibility.")  # final tip
        return 0  # success exit code

    except KeyboardInterrupt:
        say("warning", "Interrupted by user.")  # graceful Ctrl+C handling
        return 130  # conventional interrupted-process exit code
    except Exception as exc:
        say("error", f"Unexpected error: {exc}")  # catch-all failure message
        tb = traceback.format_exc().strip().splitlines()  # get traceback lines for compact reporting
        say("less_important", tb[-1] if tb else "No traceback available.")  # show last traceback line as FYI
        return 1  # generic failure exit code

def main() -> None:
    try:
        raise SystemExit(run(sys.argv))  # run program and convert return code into process exit
    except SystemExit:
        raise  # preserve normal exits exactly as intended
    except Exception as exc:
        enable_utf8_stdio()  # try to ensure output still works even during fatal startup issues
        enable_windows_ansi()  # try to keep ANSI output available even during fatal startup issues
        say("error", f"Fatal error: {exc}")  # final-resort fatal message
        raise SystemExit(1)  # generic fatal exit code

if __name__ == "__main__":
    main()  # standard script entry point
