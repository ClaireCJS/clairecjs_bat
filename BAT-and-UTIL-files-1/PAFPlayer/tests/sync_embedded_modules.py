"""Synchronize named development modules into PAFPlayer's single-file bundle."""
from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PLAYER = ROOT / "PAFPlayer.py"


def synchronize(names: list[str]) -> None:
    original = PLAYER.read_bytes()
    text = original.decode("utf-8-sig")
    for name in names:
        tree = ast.parse(text)
        source_path = (ROOT / "lockscreen" / "src" / f"{name}.py"
                       if name in {"PAFPlayer_lockscreen", "PAFPlayer_lockscreen_payload"}
                       else ROOT / "screensaver" / "src" / f"{name}.py"
                       if name == "PAFPlayer_screensaver"
                       else ROOT / "lockscreen" / f"{name.removeprefix('PAFPlayer_')}.py"
                       if name == "PAFPlayer_lockscreen_installer"
                       else ROOT / "src" / f"{name}.py")
        replacement = source_path.read_text(encoding="utf-8")
        ast.parse(replacement)
        value = next((node.value for node in tree.body
                      if isinstance(node, ast.Assign) and any(
                          isinstance(target, ast.Subscript)
                          and isinstance(target.value, ast.Name)
                          and target.value.id == "_PAF_BUNDLED_SOURCES"
                          and ast.literal_eval(target.slice) == name
                          for target in node.targets)), None)
        fallback = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "_PAF_BUNDLED_SOURCES"
                for target in node.targets
            ) and isinstance(node.value, ast.Dict):
                for key, candidate in zip(node.value.keys, node.value.values):
                    if ast.literal_eval(key) == name:
                        fallback = candidate
                        break
        value = value or fallback
        if value is None:
            raise RuntimeError(f"Bundled source not found: {name}")
        if value.lineno != value.end_lineno:
            raise RuntimeError(f"Bundled source assignment is not one line: {name}")
        lines = text.splitlines(keepends=True)
        encoded = lines[value.lineno - 1].encode("utf-8")
        lines[value.lineno - 1] = (
            encoded[:value.col_offset]
            + repr(replacement).encode("utf-8")
            + encoded[value.end_col_offset:]
        ).decode("utf-8")
        text = "".join(lines)
    ast.parse(text)
    if PLAYER.read_bytes() != original:
        raise RuntimeError("PAFPlayer.py changed concurrently; no bundle write performed")
    PLAYER.write_bytes(text.encode("utf-8"))


if __name__ == "__main__":
    modules = sys.argv[1:]
    if not modules:
        raise SystemExit("usage: sync_embedded_modules.py MODULE [MODULE ...]")
    synchronize(modules)
    print("Synchronized: " + ", ".join(modules))
