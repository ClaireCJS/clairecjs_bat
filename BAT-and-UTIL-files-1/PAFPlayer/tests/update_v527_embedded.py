"""One-time checked sync of the V527 lock-screen source layout into the single file."""
import ast
from pathlib import Path


root = Path(__file__).resolve().parents[1]
path = root / "PAFPlayer.py"
original = path.read_bytes()
text = original.decode("utf-8-sig")
tree = ast.parse(text)
name = "PAFPlayer_lockscreen"
replacement = (root / "lockscreen" / "src" / f"{name}.py").read_text(encoding="utf-8")
ast.parse(replacement)
lines = text.splitlines(keepends=True)
assignment = next(
    node
    for node in tree.body
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Subscript)
        and isinstance(target.value, ast.Name)
        and target.value.id == "_PAF_BUNDLED_SOURCES"
        and ast.literal_eval(target.slice) == name
        for target in node.targets
    )
)
value = assignment.value
assert value.lineno == value.end_lineno
line = lines[value.lineno - 1].encode("utf-8")
lines[value.lineno - 1] = (
    line[:value.col_offset] + repr(replacement).encode("utf-8") + line[value.end_col_offset:]
).decode("utf-8")
updated = "".join(lines)
ast.parse(updated)
assert path.read_bytes() == original, "Source changed concurrently; no write performed"
path.write_bytes(updated.encode("utf-8"))
print("Synchronized embedded PAFPlayer_lockscreen")
