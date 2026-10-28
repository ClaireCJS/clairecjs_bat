"""Compile the release and every bundle; check generated JS and a real read-only Steam scan."""
import ast
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace, ModuleType

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
source = (root / 'PAFPlayer.py').read_text(encoding='utf-8')
tree = ast.parse(source)
compiled = []
for name in ('PAFPlayer.py', 'tests/test_v590_locked_bass.py',
             'tests/verify_v590_locked_bass.py', 'tests/probe_v590_lock_state.py',
             'tests/test_v552_channels_and_locked_bass.py', 'tests/check_v590_build.py'):
    compile((root / name).read_text(encoding='utf-8'), str(root / name), 'exec')
    compiled.append(name)
bundles = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '_PAF_BUNDLED_SOURCES':
                bundles.update(ast.literal_eval(node.value))
            if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == '_PAF_BUNDLED_SOURCES':
                bundles[ast.literal_eval(target.slice)] = ast.literal_eval(node.value)
for name, text in bundles.items():
    compile(text, f'PAFPlayer.py::{name}', 'exec')
assert bundles['PAFPlayer_steam'] == (root / 'PAFPlayer_steam.py').read_text(encoding='utf-8')

# Extract the base HTML literal; apply the same optional augmentations without
# importing the player, acquiring ownership, touching preferences, or starting audio.
web = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_paf_web_html')
html = max((n.value for n in ast.walk(web) if isinstance(n, ast.Constant) and isinstance(n.value, str)), key=len)
js_count = 0
for name in ('PAFPlayer_workflows_ui', 'PAFPlayer_screensaver', 'PAFPlayer_lockscreen', 'PAFPlayer_tray', 'PAFPlayer_steam'):
    module = ModuleType('build_check_' + name)
    module.__file__ = str(root / (name + '.py'))
    sys.modules[module.__name__] = module
    ns = vars(module)
    exec(compile(bundles[name], name, 'exec'), ns)
    # The two newer UI modules expose augment; the workflow UI uses augment_html.
    augment = ns.get('augment') or ns.get('augment_html')
    if augment:
        html = augment(html)
for script in re.findall(r'<script[^>]*>(.*?)</script>', html, re.S):
    result = subprocess.run([r'C:\Program Files\nodejs\node.exe', '--check', '-'],
                            input=script, text=True, encoding='utf-8', capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    js_count += 1
assert js_count == 8

report = {
    'version': 'V590',
    'source_sha256': hashlib.sha256((root / 'PAFPlayer.py').read_bytes()).hexdigest(),
    'compiled_python': compiled, 'compiled_bundles': sorted(bundles),
    'javascript_blocks_checked': js_count,
    'live_lock_trace': 'tests/reports/v590-native-lock-20261020-211846.jsonl',
}
path = root / 'tests/reports' / ('v590-build-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.json')
with path.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, indent=2, ensure_ascii=False)
print(json.dumps({'report': str(path), 'bundles': len(bundles), 'js': js_count}, ensure_ascii=False))
