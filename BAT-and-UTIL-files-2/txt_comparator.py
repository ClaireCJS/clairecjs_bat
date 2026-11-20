#!/usr/bin/env python3
"""Compare text by word, in the style of srt_comparator.py."""
import difflib
import re
import subprocess
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
CONTEXT = 4


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int
    line: int


def usage():
    print('Usage: txt_comparator.py [options] file1.txt file2.txt ...')
    print('Options:')
    print('  -hi, --hide-identical-lines  Show differences with surrounding context')
    print('  -sf, --show-filenames, --key Show color/filename key for files')
    print('  -h, --help                   Show this help')


def num_label(i):
    return CIRCLED[i] if i < len(CIRCLED) else f'[{i + 1}]'


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


def render_group(rows, texts):
    segments = []
    for i, text in enumerate(texts):
        cells = [(row[i], not identical(row)) for row in rows if row[i] is not None]
        if cells:
            first, last = cells[0][0], cells[-1][0]
            span = f'line {first.line}' if first.line == last.line else f'lines {first.line}-{last.line}'
            pieces = []
            pos = first.start
            for token, changed in cells:
                pieces.append(text[pos:token.start])
                pieces.append(f'\033[7m{token.text}\033[27m' if changed else token.text)
                pos = token.end
            segments.append((i, span, ''.join(pieces)))
    heading = ' / '.join(f'{num_label(i)} {span}' for i, span, _ in segments)
    print(f'{BRIGHT_YELLOW}⸎  {heading}:{RESET}')
    for i, _, content in segments:
        label = num_label(i)
        color = COLORS[i % len(COLORS)]
        for n, line in enumerate(content.split('\n')):
            prefix = label if n == 0 else ' ' * len(label)
            print(f'    {color}{prefix}  {line}{RESET}')
    print()


def main():
    if '--plain' not in sys.argv[1:]:
        wrapper = Path(__file__).resolve().with_name('txt_comparator_columns.py')
        return subprocess.call([sys.executable, str(wrapper), *sys.argv[1:]])
    sys.argv.remove('--plain')
    hide_identical = False
    show_filenames = False
    files = []
    for arg in sys.argv[1:]:
        if arg in ('-h', '--help'):
            usage()
            return 0
        if arg in ('-hi', '--hi', '--hide-identical-lines'):
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
    texts = []
    for path in files:
        try:
            with open(path, 'r', encoding='utf-8-sig', newline=None) as file:
                texts.append(file.read())
        except (OSError, UnicodeError) as error:
            print(f'Error reading {path}: {error}', file=sys.stderr)
            return 1
    if show_filenames:
        print(f'{BRIGHT_YELLOW}⸎  Files being compared: ⸎{RESET}')
        for i, path in enumerate(files):
            print(f'    {COLORS[i % len(COLORS)]}{num_label(i)}  {path}{RESET}')
        print()
    rows = align_files([tokenize(text) for text in texts])
    for start, end in groups(rows, hide_identical):
        render_group(rows[start:end], texts)
    return 0


if __name__ == '__main__':
    sys.exit(main())
