"""Generate and embed the complete V528 lock-screen installer payload."""
import ast
import base64
import hashlib
from pathlib import Path
import zlib


root = Path(__file__).resolve().parents[1]
main_path = root / "PAFPlayer.py"
source_root = root / "lockscreen" / "src"
package = root / "lockscreen/dist/v528/PAFPlayerLockScreen_v528_x64.msix"
certificate = root / "lockscreen/dist/PAFPlayerLockScreen_v505.cer"
payload_path = source_root / "PAFPlayer_lockscreen_payload.py"

payloads = {
    package.name: package.read_bytes(),
    certificate.name: certificate.read_bytes(),
}
encoded = {
    name: base64.b85encode(zlib.compress(data, 9)).decode("ascii")
    for name, data in payloads.items()
}
digests = {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}
payload_source = (
    '"""Generated, compressed V528 lock-screen installation payload."""\n'
    'import base64\nimport zlib\n\n'
    f'PAYLOAD_SHA256 = {digests!r}\n'
    f'_PAYLOADS = {encoded!r}\n\n'
    'def payload_bytes(name):\n'
    '    if name not in _PAYLOADS:\n'
    '        raise KeyError("Unknown lock-screen payload: " + str(name))\n'
    '    data = zlib.decompress(base64.b85decode(_PAYLOADS[name]))\n'
    '    return data\n'
)
ast.parse(payload_source)
payload_path.write_text(payload_source, encoding="utf-8", newline="\n")

modules = {
    "PAFPlayer_lockscreen": (source_root / "PAFPlayer_lockscreen.py").read_text(encoding="utf-8"),
    "PAFPlayer_lockscreen_installer": (root / "lockscreen/lockscreen_installer.py").read_text(encoding="utf-8"),
    "PAFPlayer_lockscreen_payload": payload_source,
}
for value in modules.values():
    ast.parse(value)

original = main_path.read_bytes()
text = original.decode("utf-8-sig")
tree = ast.parse(text)
assignment = next(
    node for node in tree.body
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Subscript)
        and isinstance(target.value, ast.Name)
        and target.value.id == "_PAF_BUNDLED_SOURCES"
        and ast.literal_eval(target.slice) == "PAFPlayer_lockscreen"
        for target in node.targets
    )
)
value = assignment.value
assert value.lineno == value.end_lineno == assignment.lineno
lines = text.splitlines(keepends=True)
line = lines[value.lineno - 1].encode("utf-8")
lines[value.lineno - 1] = (
    line[:value.col_offset]
    + repr(modules["PAFPlayer_lockscreen"]).encode("utf-8")
    + line[value.end_col_offset:]
).decode("utf-8")

# Remove a prior generated pair, then insert the current installer and payload.
for name in ("PAFPlayer_lockscreen_installer", "PAFPlayer_lockscreen_payload"):
    prefix = f'_PAF_BUNDLED_SOURCES[{name!r}] = '
    lines = [line for line in lines if not line.startswith(prefix)]
insert_at = assignment.lineno
generated = [
    f'_PAF_BUNDLED_SOURCES[{name!r}] = {modules[name]!r}\n'
    for name in ("PAFPlayer_lockscreen_installer", "PAFPlayer_lockscreen_payload")
]
lines[insert_at:insert_at] = generated
updated = "".join(lines)
ast.parse(updated)
assert main_path.read_bytes() == original, "Source changed concurrently; no write performed"
main_path.write_bytes(updated.encode("utf-8"))
print("Embedded lock-screen source, installer, MSIX, and certificate")
