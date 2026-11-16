from pathlib import Path
import ast
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[2]
path = root / 'PAAFPlayer.py'
path = root / 'PAFPlayer.py'
tree = ast.parse(path.read_text(encoding='utf8'))
sources = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == '_PAF_BUNDLED_SOURCES':
            sources[ast.literal_eval(target.slice)] = ast.literal_eval(node.value)
for name, source in sources.items():
    compile(source, name, 'exec')
    editable = root / 'src' / (name + '.py')
    if editable.exists():
        assert editable.read_text(encoding='utf8') == source, name
assert sources
release = root / 'releases' / 'PAFPlayer_v665_dj_sleep.py'
assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(release.read_bytes()).digest()
print(f'{len(sources)} bundled modules compiled; editable sources match; release matches.')
