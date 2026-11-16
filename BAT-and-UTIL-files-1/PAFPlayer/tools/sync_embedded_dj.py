"""Refresh the generated PAFPlayer_dj source embedded in PAFPlayer.py."""
from __future__ import annotations

import ast
from pathlib import Path
import sys


def offset(text: str, lineno: int, column: int) -> int:
    lines = text.splitlines(keepends=True)
    # CPython AST columns are UTF-8 byte offsets, while Python slicing uses
    # character offsets. Embedded source strings contain non-ASCII characters.
    line = lines[lineno - 1]
    character_column = len(line.encode("utf-8")[:column].decode("utf-8"))
    return sum(len(item) for item in lines[: lineno - 1]) + character_column


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[1] / "PAFPlayer.py"
    source_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parents[1] / "src" / "PAFPlayer_dj.py"
    text = root.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(root))
    value_node = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (isinstance(target, ast.Subscript)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "_PAF_BUNDLED_SOURCES"
                        and isinstance(target.slice, ast.Constant)
                        and target.slice.value == "PAFPlayer_dj"):
                    value_node = node.value
                    break
        if value_node is not None:
            break
    if value_node is None:
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if not any(isinstance(target, ast.Name) and target.id == "_PAF_BUNDLED_SOURCES" for target in node.targets):
                continue
            if not isinstance(node.value, ast.Dict):
                continue
            for key, value in zip(node.value.keys, node.value.values):
                if isinstance(key, ast.Constant) and key.value == "PAFPlayer_dj":
                    value_node = value
                    break
            if value_node is not None:
                break
    if value_node is None:
        raise SystemExit("PAFPlayer_dj is not present in the embedded source map")
    start = offset(text, value_node.lineno, value_node.col_offset)
    end = offset(text, value_node.end_lineno, value_node.end_col_offset)
    replacement = repr(source_path.read_text(encoding="utf-8"))
    root.write_text(text[:start] + replacement + text[end:], encoding="utf-8", newline="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
