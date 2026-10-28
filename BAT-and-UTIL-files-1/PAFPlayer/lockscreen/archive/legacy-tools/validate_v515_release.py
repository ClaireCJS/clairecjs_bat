from pathlib import Path
import ast
import datetime
import hashlib
import json
import zipfile
import lockscreen_installer as installer

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'releases/PAFPlayer_v515_managed_lockscreen_manifest.json').read_text())
for name, expected in manifest['files'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
source = (root / 'PAFPlayer.py').read_bytes()
assert source == (root / 'releases/PAFPlayer_v515_managed_lockscreen.py').read_bytes()
for path in (root / 'lockscreen').glob('*.py'):
    compile(path.read_bytes(), str(path), 'exec')
old = ast.parse((root / 'releases/PAFPlayer_v514_lockscreen_background_registration.py').read_bytes())
new = ast.parse(source)
def definitions(tree):
    return {node.name: ast.dump(node, include_attributes=False) for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
before, after = definitions(old), definitions(new)
changes = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
assert len(changes) == 2 and 'PAFWebServer' in changes, changes
installer.validate_artifacts(*installer.artifacts(root / 'lockscreen'))
with zipfile.ZipFile(root / 'releases/PAFPlayer_v515_lockscreen_release_bundle.zip') as archive:
    assert archive.testzip() is None
    assert archive.read('PAFPlayer.py') == source
    assert archive.read('lockscreen/src/PAFPlayer_lockscreen.py') == (root / 'lockscreen/src/PAFPlayer_lockscreen.py').read_bytes()
report = {'releaseIntegrity': 'passed', 'sourceCompilation': 'passed',
          'changedTopLevelFunctionsOrClasses': changes,
          'packageVersion': installer.PACKAGE_VERSION, 'literalCBatChanges': [],
          'visualRendering': 'unconfirmed'}
path = root / 'tests/reports' / ('v515-release-validation-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json')
with path.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, indent=2)
print(json.dumps(report, indent=2))
print(path)
