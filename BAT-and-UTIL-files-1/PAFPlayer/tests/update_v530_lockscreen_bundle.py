"""Generate and embed the complete V530 lock-screen installer payload."""
import ast
import base64
import hashlib
from pathlib import Path
import zlib

root = Path(__file__).resolve().parents[1]
main = root / "PAFPlayer.py"
source_root = root / "lockscreen" / "src"
package = root / "lockscreen/dist/v530/PAFPlayerLockScreen_v530_x64.msix"
certificate = root / "lockscreen/dist/PAFPlayerLockScreen_v505.cer"
payload_path = source_root / "PAFPlayer_lockscreen_payload.py"
payloads = {package.name: package.read_bytes(), certificate.name: certificate.read_bytes()}
digests = {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}
encoded = {name: base64.b85encode(zlib.compress(data, 9)).decode("ascii") for name, data in payloads.items()}
payload_source = ('"""Generated, compressed V530 lock-screen installation payload."""\n'
                  'import base64\nimport zlib\n\n'
                  f'PAYLOAD_SHA256 = {digests!r}\n_PAYLOADS = {encoded!r}\n\n'
                  'def payload_bytes(name):\n'
                  '    if name not in _PAYLOADS:\n        raise KeyError("Unknown lock-screen payload: " + str(name))\n'
                  '    return zlib.decompress(base64.b85decode(_PAYLOADS[name]))\n')
ast.parse(payload_source)
payload_path.write_text(payload_source, encoding="utf-8", newline="\n")
modules = {
    "PAFPlayer_lockscreen": (source_root / "PAFPlayer_lockscreen.py").read_text(encoding="utf-8"),
    "PAFPlayer_lockscreen_installer": (root / "lockscreen/lockscreen_installer.py").read_text(encoding="utf-8"),
    "PAFPlayer_lockscreen_payload": payload_source,
    "PAFPlayer_windows_media": (root / "PAFPlayer_windows_media.py").read_text(encoding="utf-8"),
}
text = main.read_text(encoding="utf-8-sig")
tree = ast.parse(text)
assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == "_PAF_BUNDLED_SOURCES" for target in node.targets))
mapping = ast.literal_eval(assignment.value); mapping.update(modules)
lines = text.splitlines(keepends=True); line = lines[assignment.value.lineno - 1].encode("utf-8")
lines[assignment.value.lineno - 1] = (line[:assignment.value.col_offset] + repr(mapping).encode("utf-8") +
                                     line[assignment.value.end_col_offset:]).decode("utf-8")
# Remove obsolete generated post-dictionary assignments left by older generators.
for name in ("PAFPlayer_lockscreen_installer", "PAFPlayer_lockscreen_payload"):
    prefix = f'_PAF_BUNDLED_SOURCES[{name!r}] = '
    lines = [item for item in lines if not item.startswith(prefix)]
updated = "".join(lines); ast.parse(updated)
main.write_text(updated, encoding="utf-8", newline="\n")
print("Embedded V530 lock-screen source, installer, signed MSIX, certificate, and Windows media module")
