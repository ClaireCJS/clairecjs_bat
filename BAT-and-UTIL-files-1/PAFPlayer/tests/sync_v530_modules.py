"""Synchronize V530 standalone sidecars into PAFPlayer's single-file bundle."""
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
main = root / "PAFPlayer.py"
sources = {
    "PAFPlayer_windows_media": (root / "PAFPlayer_windows_media.py").read_text(encoding="utf-8"),
}
text = main.read_text(encoding="utf-8-sig")
tree = ast.parse(text)
assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == "_PAF_BUNDLED_SOURCES" for target in node.targets))
mapping = ast.literal_eval(assignment.value)
mapping.update(sources)
lines = text.splitlines(keepends=True)
line = lines[assignment.value.lineno - 1].encode("utf-8")
lines[assignment.value.lineno - 1] = (line[:assignment.value.col_offset] + repr(mapping).encode("utf-8") +
                                     line[assignment.value.end_col_offset:]).decode("utf-8")
updated = "".join(lines)
ast.parse(updated)
main.write_text(updated, encoding="utf-8", newline="\n")
print("Embedded V530 Windows media module")
