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
    * ASCII apostrophes and acute accents generally become right single quotes
      when smart apostrophes are enabled; a plain apostrophe is preserved only
      when it is acting as a feet mark in a measurement.
    * Grave accents generally become left single quotes, except when they are
      the obvious closer in a grave/accent/apostrophe pair.
    * Measurement marks such as 5'6" and 12" wide stay dumb because they are
      feet/inch symbols, not lyric punctuation. Outside that measurement
      context, apostrophes and double quotes are converted.
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
import shutil
import sys
import textwrap
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
GRAVE_ACCENT = "\u0060"
ACUTE_ACCENT = "\u00b4"

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
    GRAVE_ACCENT: DUMB_SINGLE_QUOTE,  # ````` grave accent, common apostrophe substitute
    ACUTE_ACCENT: DUMB_SINGLE_QUOTE,  # ´´´´´ acute accent, common apostrophe substitute
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
DUMB_SINGLE_QUOTE_CHARACTERS = frozenset(
    {DUMB_SINGLE_QUOTE, GRAVE_ACCENT, ACUTE_ACCENT}
)
SINGLE_QUOTE_PAIR_CLOSERS = frozenset(
    {DUMB_SINGLE_QUOTE, GRAVE_ACCENT, ACUTE_ACCENT}
)
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


def get_console_width() -> int:
    return max(60, shutil.get_terminal_size((120, 24)).columns)


def character_display_width(character: str) -> int:
    if not character:
        return 0
    if unicodedata.combining(character):
        return 0
    if unicodedata.category(character) in {"Cc", "Cf"}:
        return 0
    if unicodedata.east_asian_width(character) in {"F", "W"}:
        return 2
    return 1


def display_width(text: str) -> int:
    return sum(character_display_width(character) for character in text)


def pad_display(text: str, width: int) -> str:
    return text + " " * max(0, width - display_width(text))


def character_swatch(character: str) -> str:
    repeat_count = 3 if character_display_width(character) > 1 else 5
    return character * repeat_count


def usage_table_column_widths(console_width: int | None = None) -> list[int]:
    table_width = min(get_console_width() if console_width is None else console_width, 118)
    table_width = max(60, table_width)
    available_cell_width = table_width - 15
    character_width = 7
    codepoint_width = 6
    remaining_width = available_cell_width - character_width - codepoint_width
    name_width = min(34, max(16, remaining_width // 2))
    result_width = remaining_width - name_width

    if result_width < 12:
        name_width = max(12, name_width - (12 - result_width))
        result_width = remaining_width - name_width

    return [character_width, codepoint_width, name_width, result_width]


def wrap_table_cell(text: str, width: int) -> list[str]:
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=True,
        break_on_hyphens=False,
    ) or [""]


def table_cell_style(column_index: int, is_header: bool = False) -> str:
    if is_header:
        return f"{ANSI_BOLD}{ANSI_GREEN}"
    return [ANSI_CYAN, ANSI_BLUE, ANSI_DIM, ANSI_YELLOW][column_index]


def render_usage_table(
    headers: list[str],
    rows: list[list[str]],
    console_width: int | None = None,
) -> list[str]:
    widths = usage_table_column_widths(console_width)
    separator = (
        ANSI_DIM
        + "  +"
        + "+".join("-" * (width + 2) for width in widths)
        + "+"
        + ANSI_RESET
    )

    def render_row(cells: list[str], is_header: bool = False) -> list[str]:
        wrapped_cells = [
            wrap_table_cell(cell, width) for cell, width in zip(cells, widths)
        ]
        row_height = max(len(cell_lines) for cell_lines in wrapped_cells)
        rendered_rows = []

        for line_index in range(row_height):
            rendered_cells = []
            for column_index, (cell_lines, width) in enumerate(zip(wrapped_cells, widths)):
                cell_text = cell_lines[line_index] if line_index < len(cell_lines) else ""
                padded_cell = pad_display(cell_text, width)
                style = table_cell_style(column_index, is_header)
                rendered_cells.append(f"{style}{padded_cell}{ANSI_RESET}")
            rendered_rows.append("  | " + " | ".join(rendered_cells) + " |")

        return rendered_rows

    table_lines = [separator]
    table_lines.extend(render_row(headers, is_header=True))
    table_lines.append(separator)
    for row in rows:
        table_lines.extend(render_row(row))
    table_lines.append(separator)
    return table_lines


def character_table_row(character: str, result: str) -> list[str]:
    return [
        character_swatch(character),
        f"U+{ord(character):04X}",
        unicodedata.name(character, "unnamed character"),
        result,
    ]


def dumbifying_character_table_rows(mapping: dict[str, str]) -> list[list[str]]:
    return [
        character_table_row(character, quote_target_label(target))
        for character, target in mapping.items()
    ]


def smartening_character_table_rows() -> list[list[str]]:
    return [
        character_table_row(
            DUMB_DOUBLE_QUOTE,
            f"{LEFT_DOUBLE_QUOTE} or {RIGHT_DOUBLE_QUOTE}; opening/closing by context",
        ),
        character_table_row(
            DUMB_SINGLE_QUOTE,
            f"{RIGHT_SINGLE_QUOTE}; unless it is a feet mark",
        ),
        character_table_row(
            GRAVE_ACCENT,
            (
                f"{LEFT_SINGLE_QUOTE}; or {RIGHT_SINGLE_QUOTE} when it closes "
                "an obvious pair"
            ),
        ),
        character_table_row(
            ACUTE_ACCENT,
            f"{RIGHT_SINGLE_QUOTE}; acute accent apostrophe substitute",
        ),
    ]


def preserved_character_table_rows() -> list[list[str]]:
    return [
        character_table_row("\u2039", "preserved as a left angle expression mark"),
        character_table_row("\u203a", "preserved as a right angle expression mark"),
        character_table_row("\u00ab", "preserved as a double left angle expression mark"),
        character_table_row("\u00bb", "preserved as a double right angle expression mark"),
        character_table_row("<", "preserved in <this>-style expression text"),
        character_table_row(">", "preserved in <this>-style expression text"),
        character_table_row(
            DUMB_SINGLE_QUOTE,
            (
                "ONLY preserved as a feet mark in 5'6\" or 6' tall; otherwise "
                f"smartened to {RIGHT_SINGLE_QUOTE}"
            ),
        ),
        character_table_row(
            DUMB_DOUBLE_QUOTE,
            (
                "ONLY preserved as an inches mark in 5'6\" or 12\" wide; "
                "otherwise smartened by context"
            ),
        ),
    ]


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


def render_usage(console_width: int | None = None) -> str:
    title_header_text = "\u2728\u2731\u2728 smartquotes.py \u2728\u2731\u2728"
    usage_header_text = "\u2728\u2731\u2728 Usage: \u2728\u2731\u2728"
    flags_header_text = "\u2728\u2731\u2728 Flags: \u2728\u2731\u2728"
    algorithm_header_text = "\u2728\u2731\u2728 Algorithm: \u2728\u2731\u2728"
    examples_header_text = "\u2728\u2731\u2728 Examples: \u2728\u2731\u2728"
    smartening_converts_header_text = (
        "\u2728\u2731\u2728 Smartening Characters Converted: \u2728\u2731\u2728"
    )
    dumbifying_converts_header_text = (
        "\u2728\u2731\u2728 Dumbening Characters Converted: \u2728\u2731\u2728"
    )
    preserved_header_text = "\u2728\u2731\u2728 Characters Preserved: \u2728\u2731\u2728"
    code_header_text = "\u2728\u2731\u2728 Code Samples: \u2728\u2731\u2728"
    tests_header_text = "\u2728\u2731\u2728 Tests: \u2728\u2731\u2728"
    table_headers = ["Char", "Code", "Name", "Converts / preserves"]

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
                "  ^ Override default smartening: leave ASCII apostrophes, "
                "grave accents, and acute accents unchanged even when they "
                "would normally convert."
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
                "  3. ASCII apostrophes and ´´´´´ acute substitutes usually "
                "become right single quotes in smartening mode."
            ),
            usage_note(
                "     Plain apostrophes are preserved only as feet marks in "
                "measurements; otherwise they convert."
            ),
            usage_note(
                "  4. ````` grave accents usually become left single quotes, "
                "but close as right single quotes in obvious pairs."
            ),
            usage_note(
                "  5. Measurement marks stay plain: 5'6\", 6' tall, and "
                "12\" wide are treated as feet/inches, not quote punctuation."
            ),
            usage_note(
                "  6. Angle expression marks stay untouched: ‹this›, «this», "
                "and <this> are not quote-normalized."
            ),
            "",
            *usage_double_height_header(examples_header_text),
            "",
            usage_command(("cli", "py smartquotes.py "), ("example", '"don\'t stop"')),
            usage_note(f"  ^ -> don{RIGHT_SINGLE_QUOTE}t stop"),
            "",
            usage_command(("cli", "py smartquotes.py "), ("example", '"`til `n\' roll"')),
            usage_note(f"  ^ -> {LEFT_SINGLE_QUOTE}til {LEFT_SINGLE_QUOTE}n{RIGHT_SINGLE_QUOTE} roll"),
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
            *usage_double_height_header(smartening_converts_header_text),
            "",
            usage_note("  Default smartening mode converts these characters:"),
            *render_usage_table(
                table_headers,
                smartening_character_table_rows(),
                console_width,
            ),
            "",
            *usage_double_height_header(dumbifying_converts_header_text),
            "",
            usage_note("  --to-dumb converts these double quote characters to ASCII:"),
            *render_usage_table(
                table_headers,
                dumbifying_character_table_rows(SMART_DOUBLE_QUOTES_TO_DUMB),
                console_width,
            ),
            "",
            usage_note("  --to-dumb converts these single quote/apostrophe characters to ASCII:"),
            *render_usage_table(
                table_headers,
                dumbifying_character_table_rows(SMART_SINGLE_QUOTES_TO_DUMB),
                console_width,
            ),
            "",
            usage_note("  --to-dumb also converts these apostrophe substitutes to ASCII:"),
            *render_usage_table(
                table_headers,
                dumbifying_character_table_rows(QUOTE_SUBSTITUTES_TO_DUMB),
                console_width,
            ),
            "",
            *usage_double_height_header(preserved_header_text),
            "",
            *render_usage_table(
                table_headers,
                preserved_character_table_rows(),
                console_width,
            ),
            usage_note(
                "  Plain apostrophe is not generally preserved; it appears in "
                "this table only for the feet-mark measurement exception."
            ),
            usage_note("  <this> as a whole remains <this>; no quote conversion is applied."),
            "",
            *usage_double_height_header(code_header_text),
            "",
            usage_example_value("  import smartquotes"),
            "",
            usage_example_value('  smartquotes.smartify_quotes("don\'t stop")'),
            usage_note(f"  ^ returns don{RIGHT_SINGLE_QUOTE}t stop"),
            "",
            usage_example_value('  smartquotes.smartify_quotes("5\'6\\" and 12\\" wide")'),
            usage_note("  ^ returns 5'6\" and 12\" wide because those marks are feet/inches."),
            "",
            usage_example_value('  smartquotes.smartify_quotes("`hello\' and `til")'),
            usage_note(f"  ^ returns {LEFT_SINGLE_QUOTE}hello{RIGHT_SINGLE_QUOTE} and {LEFT_SINGLE_QUOTE}til"),
            "",
            usage_example_value("  smartquotes.smartify_quotes('\"Don\\'t,\" she said.')"),
            usage_note(f"  ^ returns {LEFT_DOUBLE_QUOTE}Don{RIGHT_SINGLE_QUOTE}t,{RIGHT_DOUBLE_QUOTE} she said."),
            "",
            usage_example_value(
                '  smartquotes.replace_dumb_quotes_with_smart_quotes("don\'t", smarten_apostrophes=False)'
            ),
            usage_note("  ^ returns don't because apostrophe smartening is explicitly disabled."),
            "",
            usage_example_value(
                f"  smartquotes.replace_smart_quotes_with_dumb_quotes('{LEFT_DOUBLE_QUOTE}Don{RIGHT_SINGLE_QUOTE}t{RIGHT_DOUBLE_QUOTE}')"
            ),
            usage_note("  ^ returns \"Don't\""),
            "",
            usage_example_value(
                f"  smartquotes.replace_smart_quotes_with_dumb_quotes('{LEFT_DOUBLE_QUOTE}quote{RIGHT_DOUBLE_QUOTE} \u2039kept\u203a \u00abkept\u00bb')"
            ),
            usage_note("  ^ returns \"quote\" ‹kept› «kept»; angle expression marks stay preserved."),
            "",
            usage_example_value("  smartquotes.contains_smart_quotes('can’t')"),
            usage_note("  ^ returns True"),
            "",
            usage_example_value("  smartquotes.contains_unconverted_dumb_quotes(\"5'6\\\"\")"),
            usage_note("  ^ returns False because the marks are measurement symbols."),
            "",
            usage_example_value("  smartquotes.contains_unconverted_dumb_quotes(\"don't\")"),
            usage_note("  ^ returns True because the apostrophe should convert."),
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


def _is_single_quote_closing_context(text: str, index: int) -> bool:
    previous = text[index - 1] if index > 0 else ""
    next_character = text[index + 1] if index < len(text) - 1 else ""
    return (
        _is_word_character(previous)
        or previous in SINGLE_QUOTE_PAIR_CLOSERS
        or previous == LEFT_SINGLE_QUOTE
    ) and _is_boundary_after_measurement_mark(next_character)


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
    """Convert dumb apostrophe-like marks while preserving measurements."""
    if text is None:
        return ""

    result = []
    in_grave_quote_pair = False
    for index, character in enumerate(text):
        if character not in DUMB_SINGLE_QUOTE_CHARACTERS:
            result.append(character)
            continue

        if _is_feet_mark_context(text, index):
            result.append(DUMB_SINGLE_QUOTE)
            in_grave_quote_pair = False
        elif character == GRAVE_ACCENT:
            if in_grave_quote_pair and _is_single_quote_closing_context(text, index):
                result.append(RIGHT_SINGLE_QUOTE)
                in_grave_quote_pair = False
            else:
                result.append(LEFT_SINGLE_QUOTE)
                in_grave_quote_pair = True
        elif in_grave_quote_pair and _is_single_quote_closing_context(text, index):
            result.append(RIGHT_SINGLE_QUOTE)
            in_grave_quote_pair = False
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
        usage = render_usage(console_width=80)
        plain_usage = re.sub(r"\033(?:\[[0-?]*[ -/]*[@-~]|#[0-9])", "", usage)
        plain_lines = plain_usage.splitlines()

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
            "Smartening Characters Converted:",
            "Dumbening Characters Converted:",
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
            self.assertTrue(
                any(
                    character_swatch(character) in line
                    and f"U+{ord(character):04X}" in line
                    for line in plain_lines
                )
            )
        for character in (
            "\u2039",
            "\u203a",
            "\u00ab",
            "\u00bb",
            "<",
            ">",
        ):
            self.assertTrue(
                any(
                    character_swatch(character) in line
                    and f"U+{ord(character):04X}" in line
                    for line in plain_lines
                )
            )

        self.assertIn("ASCII double quotes choose opening or closing curly", plain_usage)
        self.assertIn("Angle expression marks stay untouched", plain_usage)
        self.assertIn("| Char", plain_usage)
        self.assertIn("Converts /", plain_usage)
        table_lines = [
            line for line in plain_lines if line.startswith("  | ") or line.startswith("  +")
        ]
        self.assertTrue(table_lines)
        self.assertLessEqual(max(display_width(line) for line in table_lines), 80)
        self.assertLess(
            plain_usage.index("Smartening Characters Converted:"),
            plain_usage.index("Dumbening Characters Converted:"),
        )
        self.assertLess(
            plain_usage.index("Default smartening mode converts these characters:"),
            plain_usage.index("--to-dumb converts these double quote characters"),
        )
        self.assertIn("grave accents usually become left single quotes", plain_usage)
        self.assertIn("Plain apostrophes are preserved only as feet marks", plain_usage)
        self.assertIn("ONLY preserved as a feet", plain_usage)
        self.assertIn("mark in 5'6", plain_usage)
        self.assertIn("apostrophe is not generally preserved", plain_usage)
        self.assertIn("preserved as a left angle", plain_usage)
        self.assertIn("expression mark", plain_usage)
        self.assertIn("preserved in <this>-style", plain_usage)
        self.assertIn("expression text", plain_usage)
        self.assertIn("import smartquotes", plain_usage)
        self.assertIn('smartquotes.smartify_quotes("don\'t stop")', plain_usage)
        self.assertIn("smartquotes.smartify_quotes(\"5'6\\\" and 12\\\" wide\")", plain_usage)
        self.assertIn('smartquotes.smartify_quotes("`hello\' and `til")', plain_usage)
        self.assertIn("smarten_apostrophes=False", plain_usage)
        self.assertIn("angle expression marks stay preserved", plain_usage)
        self.assertIn('smartquotes.contains_unconverted_dumb_quotes("don\'t")', plain_usage)
        self.assertIn("smartquotes.smartify_quotes", plain_usage)
        self.assertIn("smartquotes.replace_smart_quotes_with_dumb_quotes", plain_usage)

    def test_usage_table_uses_display_width_for_fullwidth_characters(self) -> None:
        self.assertEqual(2, character_display_width("\uff07"))
        self.assertEqual("\uff07" * 3, character_swatch("\uff07"))
        self.assertEqual(DUMB_SINGLE_QUOTE * 5, character_swatch(DUMB_SINGLE_QUOTE))

        table = render_usage_table(
            ["Char", "Code", "Name", "Converts / preserves"],
            [character_table_row("\uff07", "ASCII apostrophe (')")],
            console_width=80,
        )
        plain_table = re.sub(
            r"\033(?:\[[0-?]*[ -/]*[@-~]|#[0-9])",
            "",
            "\n".join(table),
        )
        table_lines = plain_table.splitlines()
        self.assertTrue(any("\uff07" * 3 in line for line in table_lines))
        self.assertFalse(any("\uff07" * 5 in line for line in table_lines))
        self.assertLessEqual(max(display_width(line) for line in table_lines), 80)

    def test_usage_flag_prints_reference(self) -> None:
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = main(["--usage"])

        output = buffer.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("smartquotes.py", output)
        self.assertIn("Smartening Characters Converted:", output)
        self.assertIn("Dumbening Characters Converted:", output)

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
        self.assertNotIn(DUMB_SINGLE_QUOTE, smartify_quotes("don't 'round 1980's"))
        self.assertFalse(contains_unconverted_dumb_quotes("5'6\" and 12\" wide"))
        self.assertTrue(contains_unconverted_dumb_quotes("don't stop"))

    def test_smartify_grave_accent_opens_single_quotes_by_default(self) -> None:
        self.assertEqual(f"{LEFT_SINGLE_QUOTE}til", smartify_quotes("`til"))
        self.assertEqual(
            f"rock {LEFT_SINGLE_QUOTE}n{RIGHT_SINGLE_QUOTE} roll",
            smartify_quotes("rock `n' roll"),
        )

    def test_smartify_grave_accent_obvious_pairs(self) -> None:
        self.assertEqual(
            f"{LEFT_SINGLE_QUOTE}hello{RIGHT_SINGLE_QUOTE}",
            smartify_quotes("`hello'"),
        )
        self.assertEqual(
            f"{LEFT_SINGLE_QUOTE}hello{RIGHT_SINGLE_QUOTE}",
            smartify_quotes("`hello`"),
        )
        self.assertEqual(
            f"{LEFT_SINGLE_QUOTE}hello{RIGHT_SINGLE_QUOTE}",
            smartify_quotes("`hello\u00b4"),
        )
        self.assertEqual(
            LEFT_SINGLE_QUOTE + RIGHT_SINGLE_QUOTE,
            smartify_quotes("``"),
        )

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
                f"{LEFT_SINGLE_QUOTE}til {RIGHT_SINGLE_QUOTE}round"
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
