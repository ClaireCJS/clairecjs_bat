"""
smartquotes.py - dependency-free quote normalization helpers.

Standalone use:
    py smartquotes.py --usage
    py smartquotes.py "don't stop"
    py smartquotes.py --to-dumb "“don’t stop”"
    py smartquotes.py --self-test

Library use:
    import smartquotes
    smartquotes.smartify_quotes('"Don\'t," she said.')
    smartquotes.replace_smart_quotes_with_dumb_quotes("“Don’t,” she said.")
    smartquotes.contains_smart_quotes("can’t")

Default direction:
    Convert plain ASCII double quotes and apostrophe-like substitutes to curly
    smart quotes, while preserving existing smart typography. Apostrophes are
    smartened only when smartify_quotes() or the command-line default is used.

Dumb direction:
    --to-dumb converts the quote characters in SMART_*_QUOTES_TO_DUMB and
    QUOTE_SUBSTITUTES_TO_DUMB to ASCII quotes for diagnostics or compatibility.

Algorithm notes:
    * ASCII double quotes are opened or closed from local context.
    * ASCII apostrophes, grave accents, and acute accents become right single
      quotes when smart apostrophes are enabled.
    * Measurement marks such as 5'6" and 12" wide stay dumb because they are
      feet/inch symbols, not lyric punctuation.
    * Angle expression marks such as ‹this› and «this» are preserved; even
      though Unicode names may call them quotation marks, Claire uses them as
      non-quote expression markers.

Run py smartquotes.py --usage for the colorized reference screen with examples,
algorithm notes, converted character tables, and importable code samples.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


LEFT_DOUBLE_QUOTE = "\u201c"
RIGHT_DOUBLE_QUOTE = "\u201d"
LEFT_SINGLE_QUOTE = "\u2018"
RIGHT_SINGLE_QUOTE = "\u2019"

DUMB_DOUBLE_QUOTE = '"'
DUMB_SINGLE_QUOTE = "'"

SMART_DOUBLE_QUOTES_TO_DUMB = {
    "\u201c": DUMB_DOUBLE_QUOTE,  # “““““ left double quotation mark
    "\u201d": DUMB_DOUBLE_QUOTE,  # ””””” right double quotation mark
    "\u201e": DUMB_DOUBLE_QUOTE,  # „„„„„ double low-9 quotation mark
    "\u201f": DUMB_DOUBLE_QUOTE,  # ‟‟‟‟‟ double high-reversed-9 quotation mark
    "\u2033": DUMB_DOUBLE_QUOTE,  # ″″″″″ double prime
    "\u2036": DUMB_DOUBLE_QUOTE,  # ‶‶‶‶‶ reversed double prime
    "\u275d": DUMB_DOUBLE_QUOTE,  # ❝❝❝❝❝ heavy double turned comma quotation mark
    "\u275e": DUMB_DOUBLE_QUOTE,  # ❞❞❞❞❞ heavy double comma quotation mark ornament
    "\u301d": DUMB_DOUBLE_QUOTE,  # 〝〝〝〝〝 reversed double prime quotation mark
    "\u301e": DUMB_DOUBLE_QUOTE,  # 〞〞〞〞〞 double prime quotation mark
    "\u301f": DUMB_DOUBLE_QUOTE,  # 〟〟〟〟〟 low double prime quotation mark
    "\uff02": DUMB_DOUBLE_QUOTE,  # ＂＂＂＂＂ fullwidth quotation mark
}

SMART_SINGLE_QUOTES_TO_DUMB = {
    "\u2018": DUMB_SINGLE_QUOTE,  # ‘‘‘‘‘ left single quotation mark
    "\u2019": DUMB_SINGLE_QUOTE,  # ’’’’’ right single quotation mark / apostrophe
    "\u201a": DUMB_SINGLE_QUOTE,  # ‚‚‚‚‚ single low-9 quotation mark
    "\u201b": DUMB_SINGLE_QUOTE,  # ‘‘‘‘‘ single high-reversed-9 quotation mark
    "\u2032": DUMB_SINGLE_QUOTE,  # ′′′′′ prime
    "\u2035": DUMB_SINGLE_QUOTE,  # ‵‵‵‵‵ reversed prime
    "\u275b": DUMB_SINGLE_QUOTE,  # ❛❛❛❛❛ heavy single turned comma quotation mark
    "\u275c": DUMB_SINGLE_QUOTE,  # ❜❜❜❜❜ heavy single comma quotation mark ornament
    "\uff07": DUMB_SINGLE_QUOTE,  # ＇＇＇＇＇ fullwidth apostrophe
}

QUOTE_SUBSTITUTES_TO_DUMB = {
    "\u0060": DUMB_SINGLE_QUOTE,  # ````` grave accent, common apostrophe substitute
    "\u00b4": DUMB_SINGLE_QUOTE,  # ´´´´´ acute accent, common apostrophe substitute
}

SMART_QUOTES_TO_DUMB = {
    **SMART_DOUBLE_QUOTES_TO_DUMB,
    **SMART_SINGLE_QUOTES_TO_DUMB,
    **QUOTE_SUBSTITUTES_TO_DUMB,
}
SMART_QUOTE_TRANSLATION = str.maketrans(SMART_QUOTES_TO_DUMB)
SMART_QUOTE_CHARACTERS = frozenset(
    set(SMART_DOUBLE_QUOTES_TO_DUMB) | set(SMART_SINGLE_QUOTES_TO_DUMB)
)
DUMB_SINGLE_QUOTE_CHARACTERS = frozenset({DUMB_SINGLE_QUOTE, "\u0060", "\u00b4"})
DUMB_QUOTE_CHARACTERS = frozenset({DUMB_DOUBLE_QUOTE}) | DUMB_SINGLE_QUOTE_CHARACTERS
ANY_QUOTE_CHARACTERS = SMART_QUOTE_CHARACTERS | DUMB_QUOTE_CHARACTERS
OPENING_DOUBLE_QUOTE_CONTEXT = set("[({<\u00a1!\u00bf" + LEFT_DOUBLE_QUOTE)
DUMB_SINGLE_QUOTE_TRANSLATION = str.maketrans(
    {character: RIGHT_SINGLE_QUOTE for character in DUMB_SINGLE_QUOTE_CHARACTERS}
)

LOCAL_CORPUS_DEFAULT_ROOT = Path(r"C:\mp3")
LOCAL_CORPUS_EXTENSIONS = {".lrc", ".srt", ".txt"}

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_ITALIC = "\033[3m"
ANSI_BLINK = "\033[5m"
ANSI_CYAN = "\033[96m"
ANSI_GREEN = "\033[92m"
ANSI_BLUE = "\033[94m"
ANSI_YELLOW = "\033[93m"
ANSI_DOUBLE_HEIGHT_TOP = "\033#3"
ANSI_DOUBLE_HEIGHT_BOTTOM = "\033#4"


def usage_cli(text: str) -> str:
    return f"{ANSI_CYAN}{text}{ANSI_RESET}"


def usage_example_value(text: str) -> str:
    return f"{ANSI_BLUE}{text}{ANSI_RESET}"


def usage_note(text: str) -> str:
    return f"{ANSI_DIM}{ANSI_ITALIC}{ANSI_YELLOW}{text}{ANSI_RESET}"


def usage_command(*parts: tuple[str, str]) -> str:
    styles = {
        "cli": ANSI_CYAN,
        "example": ANSI_BLUE,
        "special": f"{ANSI_BLINK}{ANSI_CYAN}",
    }
    rendered = []
    for part_type, text in parts:
        rendered.append(f"{styles[part_type]}{text}{ANSI_RESET}")
    return "  " + "".join(rendered)


def usage_double_height_header(text: str, extra_style: str = "") -> list[str]:
    return [
        f"{ANSI_BOLD}{extra_style}{ANSI_GREEN}{ANSI_DOUBLE_HEIGHT_TOP}{text}{ANSI_RESET}",
        f"{ANSI_BOLD}{extra_style}{ANSI_GREEN}{ANSI_DOUBLE_HEIGHT_BOTTOM}{text}{ANSI_RESET}",
    ]


def quote_target_label(target: str) -> str:
    if target == DUMB_DOUBLE_QUOTE:
        return 'ASCII double quote (")'
    return "ASCII apostrophe (')"


def character_row(character: str, target: str) -> str:
    codepoint = f"U+{ord(character):04X}"
    display = character * 5
    name = unicodedata.name(character, "unnamed character")
    return (
        "  "
        f"{ANSI_CYAN}{display}{ANSI_RESET} "
        f"{ANSI_BLUE}{codepoint}{ANSI_RESET} "
        f"{ANSI_DIM}{name}{ANSI_RESET} "
        f"{ANSI_YELLOW}-> {quote_target_label(target)}{ANSI_RESET}"
    )


def character_rows(mapping: dict[str, str]) -> list[str]:
    return [character_row(character, target) for character, target in mapping.items()]


def smartening_character_rows() -> list[str]:
    rows = [
        (
            DUMB_DOUBLE_QUOTE,
            f"{LEFT_DOUBLE_QUOTE} or {RIGHT_DOUBLE_QUOTE}",
            "opening/closing smart double quote by context",
        ),
        (
            DUMB_SINGLE_QUOTE,
            RIGHT_SINGLE_QUOTE,
            "right single quote unless it is a feet mark",
        ),
        (
            "\u0060",
            RIGHT_SINGLE_QUOTE,
            "grave accent apostrophe substitute",
        ),
        (
            "\u00b4",
            RIGHT_SINGLE_QUOTE,
            "acute accent apostrophe substitute",
        ),
    ]
    rendered_rows = []
    for character, target, note in rows:
        codepoint = f"U+{ord(character):04X}"
        display = character * 5
        name = unicodedata.name(character, "unnamed character")
        rendered_rows.append(
            "  "
            f"{ANSI_CYAN}{display}{ANSI_RESET} "
            f"{ANSI_BLUE}{codepoint}{ANSI_RESET} "
            f"{ANSI_DIM}{name}{ANSI_RESET} "
            f"{ANSI_YELLOW}-> {target}{ANSI_RESET} "
            f"{ANSI_DIM}{note}{ANSI_RESET}"
        )
    return rendered_rows


def preserved_character_rows() -> list[str]:
    rows = [
        ("\u2039", "preserved as a left angle expression mark"),
        ("\u203a", "preserved as a right angle expression mark"),
        ("\u00ab", "preserved as a double left angle expression mark"),
        ("\u00bb", "preserved as a double right angle expression mark"),
        ("<", "preserved in <this>-style expression text"),
        (">", "preserved in <this>-style expression text"),
        (DUMB_SINGLE_QUOTE, "preserved as a feet mark in 5'6\" and 6' tall"),
        (DUMB_DOUBLE_QUOTE, "preserved as an inches mark in 5'6\" and 12\" wide"),
    ]
    rendered_rows = []
    for character, note in rows:
        codepoint = f"U+{ord(character):04X}"
        display = character * 5
        name = unicodedata.name(character, "unnamed character")
        rendered_rows.append(
            "  "
            f"{ANSI_CYAN}{display}{ANSI_RESET} "
            f"{ANSI_BLUE}{codepoint}{ANSI_RESET} "
            f"{ANSI_DIM}{name}{ANSI_RESET} "
            f"{ANSI_YELLOW}-> {note}{ANSI_RESET}"
        )
    return rendered_rows


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


def render_usage() -> str:
    title_header_text = "\u2728\u2731\u2728 smartquotes.py \u2728\u2731\u2728"
    usage_header_text = "\u2728\u2731\u2728 Usage: \u2728\u2731\u2728"
    flags_header_text = "\u2728\u2731\u2728 Flags: \u2728\u2731\u2728"
    algorithm_header_text = "\u2728\u2731\u2728 Algorithm: \u2728\u2731\u2728"
    examples_header_text = "\u2728\u2731\u2728 Examples: \u2728\u2731\u2728"
    converts_header_text = "\u2728\u2731\u2728 Characters Converted: \u2728\u2731\u2728"
    preserved_header_text = "\u2728\u2731\u2728 Characters Preserved: \u2728\u2731\u2728"
    code_header_text = "\u2728\u2731\u2728 Code Samples: \u2728\u2731\u2728"
    tests_header_text = "\u2728\u2731\u2728 Tests: \u2728\u2731\u2728"

    return "\n".join(
        [
            "",
            *usage_double_height_header(title_header_text, ANSI_BLINK),
            "",
            usage_note(
                "  Dependency-free quote normalization for Claire Sawyer's "
                "subtitle/lyrics tools: smarten dumb quotes by default, or "
                "dumbify known typographic quote characters with --to-dumb."
            ),
            "",
            *usage_double_height_header(usage_header_text),
            "",
            usage_command(
                ("cli", "py smartquotes.py "),
                ("example", '"text to convert"'),
                ("cli", " [flags]"),
            ),
            usage_note(
                "  ^ Convert command-line text. Default mode smartens plain "
                "ASCII quotes and apostrophe substitutes."
            ),
            "",
            usage_command(("cli", "py smartquotes.py --usage")),
            usage_note("  ^ Show this colorized reference guide."),
            "",
            usage_command(("cli", "py smartquotes.py --self-test")),
            usage_note("  ^ Run the internal unit tests and local 100-file quote corpus check."),
            "",
            *usage_double_height_header(flags_header_text),
            "",
            usage_command(("cli", "--to-dumb")),
            usage_note(
                "  ^ Convert only the listed typographic quote characters to "
                "ASCII dumb quotes; angle expression marks are preserved."
            ),
            "",
            usage_command(("cli", "--no-smart-apostrophes")),
            usage_note(
                "  ^ In default smartening mode, leave ASCII apostrophes, "
                "grave accents, and acute accents unchanged."
            ),
            "",
            usage_command(("cli", "--usage  -h  --help")),
            usage_note("  ^ Show this guide."),
            "",
            usage_command(("cli", "--self-test")),
            usage_note("  ^ Run all smartquotes unit tests."),
            "",
            *usage_double_height_header(algorithm_header_text),
            "",
            usage_note(
                "  1. Existing smart quotes stay smart; this tool does not "
                "flatten typography unless --to-dumb is requested."
            ),
            usage_note(
                "  2. ASCII double quotes choose opening or closing curly "
                "forms from nearby punctuation, words, spacing, and quote state."
            ),
            usage_note(
                "  3. ASCII apostrophes plus ````` grave and ´´´´´ acute "
                "substitutes become right single quotes in smartening mode."
            ),
            usage_note(
                "  4. Measurement marks stay plain: 5'6\", 6' tall, and "
                "12\" wide are treated as feet/inches, not quotes."
            ),
            usage_note(
                "  5. Angle expression marks stay untouched: ‹this›, «this», "
                "and <this> are not quote-normalized."
            ),
            "",
            *usage_double_height_header(examples_header_text),
            "",
            usage_command(("cli", "py smartquotes.py "), ("example", '"don\'t stop"')),
            usage_note(f"  ^ -> don{RIGHT_SINGLE_QUOTE}t stop"),
            "",
            usage_command(("cli", "py smartquotes.py "), ("example", '\'"hello"\'')),
            usage_note(f"  ^ -> {LEFT_DOUBLE_QUOTE}hello{RIGHT_DOUBLE_QUOTE}"),
            "",
            usage_command(
                ("cli", "py smartquotes.py --to-dumb "),
                ("example", f'"{LEFT_DOUBLE_QUOTE}don{RIGHT_SINGLE_QUOTE}t{RIGHT_DOUBLE_QUOTE}"'),
            ),
            usage_note("  ^ -> \"don't\""),
            "",
            usage_command(
                ("cli", "py smartquotes.py --no-smart-apostrophes "),
                ("example", '"don\'t stop"'),
            ),
            usage_note("  ^ -> don't stop"),
            "",
            usage_command(("cli", "py smartquotes.py "), ("example", '"5\'6\\" tall"')),
            usage_note("  ^ -> 5'6\" tall"),
            "",
            usage_command(("cli", "py smartquotes.py "), ("example", '"‹this› «that» <still-this>"')),
            usage_note("  ^ -> ‹this› «that» <still-this>"),
            "",
            *usage_double_height_header(converts_header_text),
            "",
            usage_note("  Default smartening mode converts these first:"),
            *smartening_character_rows(),
            "",
            usage_note("  --to-dumb converts these double quote characters to ASCII:"),
            *character_rows(SMART_DOUBLE_QUOTES_TO_DUMB),
            "",
            usage_note("  --to-dumb converts these single quote/apostrophe characters to ASCII:"),
            *character_rows(SMART_SINGLE_QUOTES_TO_DUMB),
            "",
            usage_note("  --to-dumb also converts these apostrophe substitutes to ASCII:"),
            *character_rows(QUOTE_SUBSTITUTES_TO_DUMB),
            "",
            *usage_double_height_header(preserved_header_text),
            "",
            *preserved_character_rows(),
            usage_note("  <this> as a whole remains <this>; no quote conversion is applied."),
            "",
            *usage_double_height_header(code_header_text),
            "",
            usage_example_value("  import smartquotes"),
            usage_example_value("  smartquotes.smartify_quotes('\"Don\\'t,\" she said.')"),
            usage_note(f"  ^ returns {LEFT_DOUBLE_QUOTE}Don{RIGHT_SINGLE_QUOTE}t,{RIGHT_DOUBLE_QUOTE} she said."),
            "",
            usage_example_value(
                f"  smartquotes.replace_smart_quotes_with_dumb_quotes('{LEFT_DOUBLE_QUOTE}Don{RIGHT_SINGLE_QUOTE}t{RIGHT_DOUBLE_QUOTE}')"
            ),
            usage_note("  ^ returns \"Don't\""),
            "",
            usage_example_value("  smartquotes.contains_smart_quotes('can’t')"),
            usage_note("  ^ returns True"),
            "",
            usage_example_value("  smartquotes.contains_unconverted_dumb_quotes('5\\'6\" and don\\'t')"),
            usage_note("  ^ returns True because don't still has a convertible apostrophe."),
            "",
            *usage_double_height_header(tests_header_text),
            "",
            usage_command(("cli", "py smartquotes.py --self-test")),
            usage_note(
                "  ^ Tests the mapping tables, angle-mark preservation, "
                "feet/inches handling, idempotence, and the local 100-file quote corpus."
            ),
            "",
        ]
    )


def print_usage() -> None:
    print(console_safe_text(render_usage()))


@dataclass(frozen=True)
class QuoteCorpusSample:
    path: Path
    text: str
    has_smart_quotes: bool
    has_dumb_quotes: bool


def replace_smart_quotes_with_dumb_quotes(text: str | None) -> str:
    """Convert curly/typographic quote-like characters to ASCII quotes."""
    if text is None:
        return ""
    return text.translate(SMART_QUOTE_TRANSLATION)


def normalize_smart_quotes_to_dumb_quotes(text: str | None) -> str:
    return replace_smart_quotes_with_dumb_quotes(text)


def dumbify_quotes(text: str | None) -> str:
    return replace_smart_quotes_with_dumb_quotes(text)


def count_smart_quote_characters(text: str | None) -> int:
    if not text:
        return 0
    return sum(1 for character in text if character in SMART_QUOTE_CHARACTERS)


def contains_smart_quotes(text: str | None) -> bool:
    return count_smart_quote_characters(text) > 0


def contains_dumb_quotes(text: str | None) -> bool:
    if not text:
        return False
    return any(character in DUMB_QUOTE_CHARACTERS for character in text)


def contains_any_quotes(text: str | None) -> bool:
    if not text:
        return False
    return any(character in ANY_QUOTE_CHARACTERS for character in text)


def _is_blank(character: str) -> bool:
    return character == "" or character.isspace()


def _is_punctuation(character: str) -> bool:
    if not character:
        return False
    return unicodedata.category(character).startswith("P")


def _is_punctuation_except_double_quote(character: str) -> bool:
    return character != DUMB_DOUBLE_QUOTE and _is_punctuation(character)


def _is_word_character(character: str) -> bool:
    return bool(character) and character.isalnum()


def _is_boundary_after_measurement_mark(character: str) -> bool:
    return character == "" or character.isspace() or _is_punctuation(character)


def _is_feet_mark_context(text: str, index: int) -> bool:
    previous = text[index - 1] if index > 0 else ""
    next_character = text[index + 1] if index < len(text) - 1 else ""
    return previous.isdigit() and (
        next_character.isdigit() or _is_boundary_after_measurement_mark(next_character)
    )


def _is_inches_mark_context(text: str, index: int) -> bool:
    previous = text[index - 1] if index > 0 else ""
    return previous.isdigit()


def _is_preserved_measurement_quote(text: str, index: int) -> bool:
    character = text[index]
    if character == DUMB_DOUBLE_QUOTE:
        return _is_inches_mark_context(text, index)
    if character in DUMB_SINGLE_QUOTE_CHARACTERS:
        return _is_feet_mark_context(text, index)
    return False


def count_unconverted_dumb_quote_characters(text: str | None) -> int:
    if not text:
        return 0
    return sum(
        1
        for index, character in enumerate(text)
        if character in DUMB_QUOTE_CHARACTERS
        and not _is_preserved_measurement_quote(text, index)
    )


def contains_unconverted_dumb_quotes(text: str | None) -> bool:
    return count_unconverted_dumb_quote_characters(text) > 0


def _choose_smart_double_quote(
    text: str,
    index: int,
    in_quotes: bool,
    last_non_space: str,
) -> tuple[str, bool]:
    previous = text[index - 1] if index > 0 else ""
    next_character = text[index + 1] if index < len(text) - 1 else ""
    next_next_character = text[index + 2] if index < len(text) - 2 else ""

    if _is_inches_mark_context(text, index):
        return DUMB_DOUBLE_QUOTE, False

    if previous in OPENING_DOUBLE_QUOTE_CONTEXT:
        return LEFT_DOUBLE_QUOTE, True

    if _is_blank(previous) and _is_blank(next_character):
        if last_non_space == RIGHT_DOUBLE_QUOTE:
            return LEFT_DOUBLE_QUOTE, True
        if last_non_space == LEFT_DOUBLE_QUOTE:
            return RIGHT_DOUBLE_QUOTE, False
        if (
            (
                _is_punctuation(last_non_space)
                and last_non_space != LEFT_DOUBLE_QUOTE
                and _is_word_character(next_next_character)
            )
            or (
                _is_word_character(last_non_space)
                and _is_word_character(next_next_character)
            )
        ):
            return LEFT_DOUBLE_QUOTE, True
        return RIGHT_DOUBLE_QUOTE, False

    if previous == " " and _is_word_character(next_character) and last_non_space != ".":
        return LEFT_DOUBLE_QUOTE, True

    if _is_punctuation_except_double_quote(previous) or _is_word_character(previous):
        return RIGHT_DOUBLE_QUOTE, False

    if (previous == "" or _is_punctuation_except_double_quote(previous)) and (
        last_non_space != LEFT_DOUBLE_QUOTE
    ):
        return LEFT_DOUBLE_QUOTE, True

    return (RIGHT_DOUBLE_QUOTE, False) if in_quotes else (LEFT_DOUBLE_QUOTE, True)


def replace_dumb_double_quotes_with_smart_quotes(text: str | None) -> str:
    """Convert ASCII double quotes to curly double quotes using local context."""
    if text is None or text == "":
        return ""
    if text == DUMB_DOUBLE_QUOTE:
        return LEFT_DOUBLE_QUOTE
    if text == DUMB_DOUBLE_QUOTE * 2:
        return LEFT_DOUBLE_QUOTE + RIGHT_DOUBLE_QUOTE

    result = []
    in_quotes = False
    last_non_space = ""

    for index, character in enumerate(text):
        if character == LEFT_DOUBLE_QUOTE:
            in_quotes = True
            character_used = character
        elif character == RIGHT_DOUBLE_QUOTE:
            in_quotes = False
            character_used = character
        elif character == DUMB_DOUBLE_QUOTE:
            character_used, in_quotes = _choose_smart_double_quote(
                text,
                index,
                in_quotes,
                last_non_space,
            )
        else:
            character_used = character

        result.append(character_used)

        if not character.isspace():
            if character_used in {LEFT_DOUBLE_QUOTE, RIGHT_DOUBLE_QUOTE}:
                last_non_space = character_used
            else:
                last_non_space = character

    return "".join(result)


def replace_ascii_apostrophes_with_smart_apostrophes(text: str | None) -> str:
    """Match the old SRT2TXT behavior: dumb apostrophes become right singles."""
    if text is None:
        return ""

    result = []
    for index, character in enumerate(text):
        if character not in DUMB_SINGLE_QUOTE_CHARACTERS:
            result.append(character)
            continue

        if _is_feet_mark_context(text, index):
            result.append(DUMB_SINGLE_QUOTE)
        else:
            result.append(RIGHT_SINGLE_QUOTE)

    return "".join(result)


def replace_dumb_quotes_with_smart_quotes(
    text: str | None,
    smarten_apostrophes: bool = False,
) -> str:
    text = replace_dumb_double_quotes_with_smart_quotes(text)
    if smarten_apostrophes:
        text = replace_ascii_apostrophes_with_smart_apostrophes(text)
    return text


def replace_quotes_with_smart_quotes(text: str | None) -> str:
    return replace_dumb_quotes_with_smart_quotes(text)


def replace_smart_quotes(text: str | None) -> str:
    return replace_dumb_quotes_with_smart_quotes(text)


def smartify_quotes(text: str | None) -> str:
    return replace_dumb_quotes_with_smart_quotes(text, smarten_apostrophes=True)


def _decode_text_bytes(raw_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def _read_text_for_corpus(path: Path, max_bytes: int = 1_000_000) -> str:
    with path.open("rb") as input_file:
        return _decode_text_bytes(input_file.read(max_bytes))


def _iter_sidecar_files(root: Path) -> Iterable[Path]:
    for current_root, directory_names, file_names in os.walk(root):
        directory_names[:] = sorted(
            directory_name
            for directory_name in directory_names
            if directory_name not in {".git", "__pycache__"}
        )
        for file_name in sorted(file_names):
            path = Path(current_root) / file_name
            lowered_name = file_name.lower()
            if path.suffix.lower() not in LOCAL_CORPUS_EXTENSIONS:
                continue
            if lowered_name.endswith("~") or ".bak." in lowered_name:
                continue
            yield path


def collect_local_quote_corpus(
    root: Path = LOCAL_CORPUS_DEFAULT_ROOT,
    limit: int = 100,
) -> list[QuoteCorpusSample]:
    """Collect quote-bearing lyric/subtitle/text files for local corpus tests."""
    smart_samples: list[QuoteCorpusSample] = []
    dumb_samples: list[QuoteCorpusSample] = []
    target_per_kind = max(1, limit // 2)

    for path in _iter_sidecar_files(root):
        try:
            text = _read_text_for_corpus(path)
        except OSError:
            continue

        has_smart = contains_smart_quotes(text)
        has_dumb = contains_dumb_quotes(text)
        if not (has_smart or has_dumb):
            continue

        sample = QuoteCorpusSample(
            path=path,
            text=text,
            has_smart_quotes=has_smart,
            has_dumb_quotes=has_dumb,
        )
        if has_smart and len(smart_samples) < target_per_kind:
            smart_samples.append(sample)
        elif has_dumb and len(dumb_samples) < limit - len(smart_samples):
            dumb_samples.append(sample)

        if (
            len(smart_samples) + len(dumb_samples) >= limit
            and smart_samples
            and dumb_samples
        ):
            break

    return (smart_samples + dumb_samples)[:limit]


class SmartQuotesUnitTests(unittest.TestCase):
    def test_each_smart_double_quote_maps_to_ascii_double_quote(self) -> None:
        for smart_quote in SMART_DOUBLE_QUOTES_TO_DUMB:
            with self.subTest(codepoint=f"U+{ord(smart_quote):04X}"):
                self.assertEqual(
                    DUMB_DOUBLE_QUOTE,
                    replace_smart_quotes_with_dumb_quotes(smart_quote),
                )

    def test_each_smart_single_quote_maps_to_ascii_single_quote(self) -> None:
        for smart_quote in SMART_SINGLE_QUOTES_TO_DUMB:
            with self.subTest(codepoint=f"U+{ord(smart_quote):04X}"):
                self.assertEqual(
                    DUMB_SINGLE_QUOTE,
                    replace_smart_quotes_with_dumb_quotes(smart_quote),
                )

    def test_each_quote_substitute_maps_to_ascii_single_quote_when_dumbifying(self) -> None:
        for quote_substitute in QUOTE_SUBSTITUTES_TO_DUMB:
            with self.subTest(codepoint=f"U+{ord(quote_substitute):04X}"):
                self.assertEqual(
                    DUMB_SINGLE_QUOTE,
                    replace_smart_quotes_with_dumb_quotes(quote_substitute),
                )

    def test_dumbifying_mixed_quotes(self) -> None:
        self.assertEqual(
            '"Don\'t", she said, \u00abit\'s 5\'6".\u00bb',
            replace_smart_quotes_with_dumb_quotes(
                "\u201cDon\u2019t\u201d, she said, \u00abit\u2019s 5\u20326\u2033.\u00bb"
            ),
        )

    def test_dumbifying_is_idempotent(self) -> None:
        text = "\u2018Hello\u2019, \u201cworld\u201d, `again\u00b4."
        once = replace_smart_quotes_with_dumb_quotes(text)
        twice = replace_smart_quotes_with_dumb_quotes(once)
        self.assertEqual(once, twice)

    def test_dumb_quotes_are_preserved_when_dumbifying(self) -> None:
        text = '"Already dumb," isn\'t it?'
        self.assertEqual(text, replace_smart_quotes_with_dumb_quotes(text))

    def test_contains_smart_quotes(self) -> None:
        self.assertTrue(contains_smart_quotes("can\u2019t"))
        self.assertFalse(contains_smart_quotes("can't"))

    def test_angle_marks_are_not_quote_normalized(self) -> None:
        text = "\u2039this\u203a \u2039is\u203a \u2039not quotes\u203a \u00abalso this\u00bb"
        self.assertEqual(text, replace_smart_quotes_with_dumb_quotes(text))
        self.assertEqual(text, smartify_quotes(text))
        self.assertFalse(contains_smart_quotes(text))
        self.assertNotIn("\u2039", SMART_SINGLE_QUOTES_TO_DUMB)
        self.assertNotIn("\u203a", SMART_SINGLE_QUOTES_TO_DUMB)
        self.assertNotIn("\u00ab", SMART_DOUBLE_QUOTES_TO_DUMB)
        self.assertNotIn("\u00bb", SMART_DOUBLE_QUOTES_TO_DUMB)

    def test_render_usage_is_a_standalone_reference(self) -> None:
        usage = render_usage()
        plain_usage = re.sub(r"\033(?:\[[0-?]*[ -/]*[@-~]|#[0-9])", "", usage)

        self.assertGreaterEqual(usage.count(ANSI_DOUBLE_HEIGHT_TOP), 8)
        self.assertGreaterEqual(usage.count(ANSI_DOUBLE_HEIGHT_BOTTOM), 8)
        self.assertIn(ANSI_GREEN, usage)
        self.assertIn(ANSI_CYAN, usage)
        self.assertIn(ANSI_BLUE, usage)
        self.assertIn(ANSI_YELLOW, usage)
        self.assertIn(ANSI_ITALIC, usage)
        self.assertIn(ANSI_BLINK, usage)

        for section in (
            "smartquotes.py",
            "Usage:",
            "Flags:",
            "Algorithm:",
            "Examples:",
            "Characters Converted:",
            "Characters Preserved:",
            "Code Samples:",
            "Tests:",
        ):
            self.assertIn(section, plain_usage)

        for option in ("--to-dumb", "--no-smart-apostrophes", "--usage", "--self-test", "--help"):
            self.assertIn(option, plain_usage)

        for character in SMART_QUOTES_TO_DUMB:
            self.assertIn(f"U+{ord(character):04X}", plain_usage)
        for character in (DUMB_DOUBLE_QUOTE, DUMB_SINGLE_QUOTE, "\u0060", "\u00b4"):
            self.assertIn(f"{character * 5} U+{ord(character):04X}", plain_usage)
        for character in (
            "\u2039",
            "\u203a",
            "\u00ab",
            "\u00bb",
            "<",
            ">",
        ):
            self.assertIn(f"{character * 5} U+{ord(character):04X}", plain_usage)

        self.assertIn("ASCII double quotes choose opening or closing curly", plain_usage)
        self.assertIn("Angle expression marks stay untouched", plain_usage)
        self.assertLess(
            plain_usage.index("Default smartening mode converts these first:"),
            plain_usage.index("--to-dumb converts these double quote characters"),
        )
        self.assertIn("preserved as a left angle expression mark", plain_usage)
        self.assertIn("preserved in <this>-style expression text", plain_usage)
        self.assertIn("import smartquotes", plain_usage)
        self.assertIn("smartquotes.smartify_quotes", plain_usage)
        self.assertIn("smartquotes.replace_smart_quotes_with_dumb_quotes", plain_usage)

    def test_usage_flag_prints_reference(self) -> None:
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = main(["--usage"])

        output = buffer.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("smartquotes.py", output)
        self.assertIn("Characters Converted:", output)

    def test_smartify_single_double_quote_matches_existing_perl_edge_case(self) -> None:
        self.assertEqual(LEFT_DOUBLE_QUOTE, replace_dumb_quotes_with_smart_quotes('"'))

    def test_smartify_empty_pair_matches_existing_perl_edge_case(self) -> None:
        self.assertEqual(
            LEFT_DOUBLE_QUOTE + RIGHT_DOUBLE_QUOTE,
            replace_dumb_quotes_with_smart_quotes('""'),
        )

    def test_smartify_balanced_double_quotes(self) -> None:
        self.assertEqual(
            f"She said {LEFT_DOUBLE_QUOTE}hello{RIGHT_DOUBLE_QUOTE}.",
            replace_dumb_quotes_with_smart_quotes('She said "hello".'),
        )

    def test_smartify_after_opening_punctuation(self) -> None:
        self.assertEqual(
            f"({LEFT_DOUBLE_QUOTE}hello{RIGHT_DOUBLE_QUOTE})",
            replace_dumb_quotes_with_smart_quotes('("hello")'),
        )

    def test_smartify_apostrophes_is_explicit(self) -> None:
        self.assertEqual(
            "don't",
            replace_dumb_quotes_with_smart_quotes("don't"),
        )
        self.assertEqual(
            f"don{RIGHT_SINGLE_QUOTE}t",
            replace_dumb_quotes_with_smart_quotes("don't", smarten_apostrophes=True),
        )

    def test_smartify_preserves_feet_and_inches_marks(self) -> None:
        self.assertEqual("5'6\"", smartify_quotes("5'6\""))
        self.assertEqual("6'0\" tall", smartify_quotes("6'0\" tall"))
        self.assertEqual("6' tall", smartify_quotes("6' tall"))
        self.assertEqual("The board is 12\" wide.", smartify_quotes("The board is 12\" wide."))

    def test_smartify_measurement_exception_does_not_block_words(self) -> None:
        self.assertEqual(f"don{RIGHT_SINGLE_QUOTE}t", smartify_quotes("don't"))
        self.assertEqual(f"{RIGHT_SINGLE_QUOTE}round", smartify_quotes("'round"))
        self.assertEqual(f"1980{RIGHT_SINGLE_QUOTE}s", smartify_quotes("1980's"))
        self.assertFalse(contains_unconverted_dumb_quotes("5'6\" and 12\" wide"))
        self.assertTrue(contains_unconverted_dumb_quotes("don't stop"))

    def test_smartify_preserves_existing_smart_quotes(self) -> None:
        text = (
            f"{LEFT_DOUBLE_QUOTE}Smart{RIGHT_DOUBLE_QUOTE} "
            f"{LEFT_SINGLE_QUOTE}single{RIGHT_SINGLE_QUOTE} "
            "\u00abangle\u00bb 5\u20326\u2033"
        )
        self.assertEqual(text, smartify_quotes(text))

    def test_smartify_converts_dumb_quotes_to_smart_quotes(self) -> None:
        self.assertEqual(
            (
                f"{LEFT_DOUBLE_QUOTE}Don{RIGHT_SINGLE_QUOTE}t,{RIGHT_DOUBLE_QUOTE} "
                f"she said, {LEFT_DOUBLE_QUOTE}it{RIGHT_SINGLE_QUOTE}s "
                f"5'6\".{RIGHT_DOUBLE_QUOTE} "
                f"{RIGHT_SINGLE_QUOTE}til {RIGHT_SINGLE_QUOTE}round"
            ),
            smartify_quotes('"Don\'t," she said, "it\'s 5\'6"." `til \u00b4round'),
        )

    def test_local_quote_corpus_smartens_at_least_100_files(self) -> None:
        if os.environ.get("SMARTQUOTES_SKIP_LOCAL_CORPUS") == "1":
            self.skipTest("SMARTQUOTES_SKIP_LOCAL_CORPUS is set")

        root = Path(os.environ.get("SMARTQUOTES_CORPUS_ROOT", str(LOCAL_CORPUS_DEFAULT_ROOT)))
        if not root.exists():
            self.skipTest(f"local quote corpus root does not exist: {root}")

        corpus = collect_local_quote_corpus(root, limit=100)
        self.assertGreaterEqual(len(corpus), 100)
        self.assertTrue(any(sample.has_smart_quotes for sample in corpus))
        self.assertTrue(any(sample.has_dumb_quotes for sample in corpus))

        for sample in corpus:
            with self.subTest(path=str(sample.path)):
                smartened = smartify_quotes(sample.text)
                for smart_quote in SMART_QUOTE_CHARACTERS:
                    self.assertGreaterEqual(
                        smartened.count(smart_quote),
                        sample.text.count(smart_quote),
                    )
                self.assertFalse(contains_unconverted_dumb_quotes(smartened))
                self.assertEqual(smartened, smartify_quotes(smartened))
                if sample.has_dumb_quotes:
                    self.assertNotEqual(sample.text, smartened)


def load_unit_tests() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(SmartQuotesUnitTests)


def run_self_test() -> None:
    result = unittest.TextTestRunner(verbosity=2).run(load_unit_tests())
    if not result.wasSuccessful():
        raise AssertionError("SmartQuotes self-test failed.")
    print("SmartQuotes self-test passed.")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert quote characters between smart and dumb forms.",
        add_help=False,
    )
    parser.add_argument("text", nargs="*", help="Text to convert")
    parser.add_argument(
        "--to-dumb",
        action="store_true",
        help="Convert smart/typographic quotes to ASCII dumb quotes",
    )
    parser.add_argument(
        "--no-smart-apostrophes",
        action="store_true",
        help="When smartening, leave ASCII apostrophes alone",
    )
    parser.add_argument("--usage", action="store_true", help="Show the rich usage guide")
    parser.add_argument("-h", "--help", action="store_true", help="Show the rich usage guide")
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests")
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_argument_parser()
    args = parser.parse_args(raw_argv)

    if not raw_argv or args.usage or args.help:
        print_usage()
        return 0

    if args.self_test:
        run_self_test()
        return 0

    if not args.text:
        print_usage()
        return 1

    text = " ".join(args.text)

    if args.to_dumb:
        print(replace_smart_quotes_with_dumb_quotes(text))
    else:
        print(
            replace_dumb_quotes_with_smart_quotes(
                text,
                smarten_apostrophes=not args.no_smart_apostrophes,
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
