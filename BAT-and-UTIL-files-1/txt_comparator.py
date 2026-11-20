#!/usr/bin/env python3
"""Compare text by word, in the style of srt_comparator.py."""
import difflib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

COLORS = [
    "\033[31m", "\033[32m", "\033[33m", "\033[34m",
    "\033[35m", "\033[36m", "\033[91m", "\033[92m",
    "\033[93m", "\033[94m", "\033[95m", "\033[96m"
]
BRIGHT_YELLOW = "\033[93m"
RESET = "\033[0m"
CIRCLED = ["❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽", "❾", "❿"]
TOKEN_RE = re.compile(r"\w+(?:['’]\w+)*|[^\w\s]", re.UNICODE)
TIMING_RE = re.compile(r'^\s*(?:\d+:)?\d{2}:\d{2}[,.]\d+\s*-->\s*(?:\d+:)?\d{2}:\d{2}[,.]\d+')
CONTEXT = 4
MAX_GROUP_TOKENS = 28
maximum_number_of_words_to_blink = 3


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int
    line: int


def usage():
    print('Usage: txt_comparator.py [options] file1.txt file2.txt ...')
    print('Options:')
    print('  --fix TARGET [via] SOURCE [with punctuation NUMBER]  Default: 2 via 1 with punctuation 1')
    print('  --include-deletions, -id     Allow removing extra target words')
    print('  -hi, --hide-identical-lines  Show differences with surrounding context')
    print('  -sf, --show-filenames, --key Show color/filename key for files')
    print('  --all                       Include matching passages')
    print('  --plain                     Stack each file instead of side by side')
    print('  -h, --help                   Show this help')


def num_label(i):
    return CIRCLED[i] if i < len(CIRCLED) else f'[{i + 1}]'


def subtitle_text(text, extension):
    """Remove subtitle metadata, preserving line breaks for source locations."""
    lines = text.splitlines(keepends=True)
    ignored = set()
    vtt = extension.lower() == '.vtt'
    in_vtt_metadata = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#'):
            ignored.add(i)
            continue
        if vtt and in_vtt_metadata:
            ignored.add(i)
            if not stripped:
                in_vtt_metadata = False
            continue
        if vtt and (stripped == 'WEBVTT' or stripped.startswith('WEBVTT ')):
            ignored.add(i)
            continue
        if vtt and re.match(r'^(NOTE(?:\s|$)|STYLE\s*$|REGION\s*$)', stripped):
            ignored.add(i)
            in_vtt_metadata = True
            continue
        if TIMING_RE.match(line):
            ignored.add(i)
            if i and (vtt or lines[i - 1].strip().isdigit()):
                ignored.add(i - 1)
    return ''.join(re.sub(r'[^\r\n]', ' ', line) if i in ignored else line
                   for i, line in enumerate(lines))


def tokenize(text):
    tokens = []
    line = 1
    previous = 0
    for match in TOKEN_RE.finditer(text):
        line += text.count('\n', previous, match.start())
        tokens.append(Token(match.group(), match.start(), match.end(), line))
        previous = match.end()
    return tokens


def align_files(contents):
    """Progressively align tokens, retaining their original positions in each file."""
    rows = [[token] for token in contents[0]]
    for file_index, tokens in enumerate(contents[1:], 1):
        reference = [next(cell.text for cell in row if cell is not None) for row in rows]
        matcher = difflib.SequenceMatcher(None, reference, [token.text for token in tokens], autojunk=False)
        merged = []
        for tag, a_start, a_end, b_start, b_end in matcher.get_opcodes():
            if tag == 'equal':
                merged.extend(row + [token] for row, token in zip(rows[a_start:a_end], tokens[b_start:b_end]))
            elif tag == 'delete':
                merged.extend(row + [None] for row in rows[a_start:a_end])
            elif tag == 'insert':
                merged.extend([None] * file_index + [token] for token in tokens[b_start:b_end])
            else:
                for offset in range(max(a_end - a_start, b_end - b_start)):
                    row = rows[a_start + offset] if a_start + offset < a_end else [None] * file_index
                    token = tokens[b_start + offset] if b_start + offset < b_end else None
                    merged.append(row + [token])
        rows = merged
    return rows


def identical(row):
    return all(cell is not None for cell in row) and len({cell.text for cell in row}) == 1


def groups(rows, hide_identical):
    """Build runs, adding and merging nearby context around differences when requested."""
    if not rows:
        return []
    different = [not identical(row) for row in rows]
    if hide_identical:
        spans = []
        for i, changed in enumerate(different):
            if changed:
                start, end = max(0, i - CONTEXT), min(len(rows), i + CONTEXT + 1)
                if spans and start <= spans[-1][1]:
                    spans[-1] = (spans[-1][0], max(spans[-1][1], end))
                else:
                    spans.append((start, end))
        return spans
    spans = []
    start = 0
    for i in range(1, len(rows)):
        if different[i] != different[start]:
            spans.append((start, i))
            start = i
    spans.append((start, len(rows)))
    return spans


def split_large_groups(rows, spans):
    """Break long differences into short, readable sections at shared-word anchors."""
    chunks = []
    for start, end in spans:
        cursor = start
        while end - cursor > MAX_GROUP_TOKENS:
            limit = min(cursor + MAX_GROUP_TOKENS, end - 1)
            # Prefer a boundary between matching tokens near the chunk limit.
            boundaries = [i for i in range(cursor + 1, limit + 1)
                          if identical(rows[i - 1]) and identical(rows[i])]
            boundary = boundaries[-1] if boundaries else limit
            chunks.append((cursor, boundary))
            cursor = boundary
        if cursor < end:
            chunks.append((cursor, end))
    return chunks


def blink_variants(rows):
    """Classify whole changed runs before splitting them for display."""
    blinking = set()
    start = 0
    while start < len(rows):
        if identical(rows[start]):
            start += 1
            continue
        end = start + 1
        while end < len(rows) and not identical(rows[end]):
            end += 1
        for file_index in range(1, len(rows[start])):
            tokens = [row[file_index] for row in rows[start:end] if row[file_index] is not None]
            words = sum(bool(re.search(r'\w', token.text)) for token in tokens)
            if 1 <= words <= maximum_number_of_words_to_blink:
                blinking.update((file_index, token.start) for token in tokens)
        start = end
    return blinking


def comparison_blocks(rows, texts, blinking, spans, reference):
    """Project reference line boundaries onto every aligned version."""
    first_line = next((row[reference].line for row in rows if row[reference] is not None), 1)
    locations = []
    line = first_line
    for row in rows:
        if row[reference] is not None:
            line = row[reference].line
        locations.append(line)
    blocks = []
    for number, (start, end) in enumerate(spans, 1):
        first, last = locations[start], locations[end - 1]
        location = f'ref line {first}' if first == last else f'ref lines {first}-{last}'
        headings = [f'#{number} {num_label(i)} {location}' for i in range(len(texts))]
        display_rows = []
        previous = [None] * len(texts)
        for index in range(start, end):
            row = rows[index]
            cells = []
            shared = identical(row)
            for i, token in enumerate(row):
                if token is None:
                    cells.append(None)
                    continue
                gap = ' ' if previous[i] is not None and texts[i][previous[i].end:token.start] else ''
                style = '\033[2m' if shared else '\033[1m'
                if (i, token.start) in blinking:
                    style += '\033[5m'
                cells.append((gap, token.text, COLORS[i % len(COLORS)] + style))
                previous[i] = token
            boundary = index > start and locations[index] != locations[index - 1]
            display_rows.append((boundary, cells))
        blocks.append((headings, display_rows))
    return blocks


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    from txt_comparator_reconcile import fix_options, reconcile
    try:
        args, target, source, punctuation, include_deletions = fix_options(sys.argv[1:])
    except (ValueError, IndexError):
        print('Error: use --fix TARGET [via] SOURCE [with punctuation NUMBER]')
        return 1
    plain = '--plain' in args
    hide_identical = not plain
    show_filenames = True
    files = []
    for arg in args:
        if arg in ('-h', '--help'):
            usage()
            return 0
        if arg == '--plain':
            continue
        if arg == '--all':
            hide_identical = False
        elif arg in ('-hi', '--hi', '--hide-identical-lines'):
            hide_identical = True
        elif arg in ('-sf', '--sf', '--show-filenames', '--key', '-key'):
            show_filenames = True
        elif arg.startswith('-'):
            print(f'Error: unknown option: {arg}', file=sys.stderr)
            usage()
            return 1
        else:
            files.append(arg)
    if len(files) < 2:
        print('Error: at least two files are required.', file=sys.stderr)
        usage()
        return 1
    if any(i < 0 or i >= len(files) for i in (target, source, punctuation)) or target == source:
        print('Error: fix indices must name existing files; target and source must differ.')
        return 1
    texts = []
    originals = []
    for path in files:
        try:
            original = Path(path).read_bytes()
            text = original.decode('utf-8-sig')
            originals.append(original)
            extension = Path(path).suffix.lower()
            texts.append(subtitle_text(text, extension) if extension in ('.srt', '.vtt') else text)
        except (OSError, UnicodeError) as error:
            print(f'Error reading {path}: {error}', file=sys.stderr)
            return 1
    if show_filenames:
        print(f'{BRIGHT_YELLOW}⸎  Files being compared: ⸎{RESET}')
        for i, path in enumerate(files):
            print(f'    {COLORS[i % len(COLORS)]}{num_label(i)}  {path}{RESET}')
        print()
    rows = align_files([tokenize(text) for text in texts])
    blinking = blink_variants(rows)
    spans = split_large_groups(rows, groups(rows, hide_identical))
    if not spans:
        print('No word or punctuation differences found.')
    reference = next((i for i, path in enumerate(files) if Path(path).suffix.lower() not in ('.srt', '.vtt')), 0)
    if spans:
        print(f'Reference line breaks: {num_label(reference)} (all versions reflowed to this text)')
        from txt_comparator_columns import render_blocks
        render_blocks(comparison_blocks(rows, texts, blinking, spans, reference), plain=plain)
    print(f'\nReconcile {num_label(target)} via {num_label(source)}, punctuation {num_label(punctuation)}; deletions {"enabled" if include_deletions else "disabled"}.')
    if sys.stdin.isatty():
        try:
            reconcile(files[target], originals[target], texts[source], texts[target], texts[punctuation], include_deletions)
        except OSError as error:
            print(f'Error saving correction: {error}', file=sys.stderr)
            return 1
    else:
        print('Interactive input unavailable; no files modified.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
