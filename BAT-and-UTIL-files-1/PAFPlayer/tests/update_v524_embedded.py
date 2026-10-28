"""One-time checked sync of the V524 tray-hover source into the single file."""
import ast
from pathlib import Path


root = Path(__file__).resolve().parents[1]
path = root / "PAFPlayer.py"
original = path.read_bytes()
text = original.decode("utf-8-sig")
tree = ast.parse(text)
bundle = next(
    node.value
    for node in tree.body
    if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == "_PAF_BUNDLED_SOURCES" for target in node.targets)
)
sources = ast.literal_eval(bundle)
name = "PAFPlayer_tray_hover"
replacement = (root / f"{name}.py").read_text(encoding="utf-8")
ast.parse(replacement)
sources[name] = replacement

lines = text.splitlines(keepends=True)
value = next(value for key, value in zip(bundle.keys, bundle.values) if ast.literal_eval(key) == name)
assert value.lineno == value.end_lineno
line = lines[value.lineno - 1].encode("utf-8")
lines[value.lineno - 1] = (
    line[:value.col_offset] + repr(replacement).encode("utf-8") + line[value.end_col_offset:]
).decode("utf-8")
updated = "".join(lines)
ast.parse(updated)
assert path.read_bytes() == original, "Source changed concurrently; no write performed"
path.write_bytes(updated.encode("utf-8"))
print("Synchronized embedded PAFPlayer_tray_hover")
