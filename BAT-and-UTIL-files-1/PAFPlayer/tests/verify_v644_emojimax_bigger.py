"""Focused curation checks in preserved, write-guarded staging."""
import ast
import contextlib
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from run_PAFPlayer_tests import install_guards, unique

root = Path(__file__).resolve().parents[1]
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
stage = unique(root/'tests/runs'/('checks-v644-'+stamp))
stage.mkdir(parents=True)
with (stage/'PAFPlayer.py').open('xb') as f:
    f.write((root/'PAFPlayer.py').read_bytes())
for key in ('APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP'):
    os.environ[key] = str(stage)
os.environ['PLAY_AUDIO_FILE_HISTORY_DB'] = str(stage/'history.sqlite3')
tempfile.tempdir = str(stage)
sys.path.insert(0, str(stage))
sys.argv = ['PAFPlayer.py', '--unit-tests']
os.chdir(stage)
blocks = install_guards(root/'tests')
import PAFPlayer as app

assert 'bigger' not in app.semantic and 'bigger' not in app.SEMANTIC_PHRASES
checks = []
for text in ('bigger', 'Bigger', 'BIGGER', 'bigger!', '(Bigger)', 'bigger BIGGER'):
    assert app.emojimax_plain_with_solutions(text) == (text, []), text
    assert app.stylize_karaoke_with_emojimax(text, 1, True, force_emoji_when_enabled=True) == text, text
    assert app.stylize_web_karaoke_with_emojimax(text, 1, True) == text, text
    checks.append(text)
assert app.emojimax_replacement_for_key('biggest') == '🦣'
names = ('test_v450_emojimaxx_cow_and_lotus_curation',
         'test_v532_emojimaxx_removes_the_bad_stripe_mappings',
         'test_v321_removes_four_requested_emojimaxx_associations',
         'test_v367_emojimaxx_curated_remove_planets_and_add_shine')
report = unique(root/'tests/reports'/('v644-checks-'+stamp+'.json'))
with report.with_suffix('.log').open('x', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.TestSuite(app.PlayWaveFileTests(n) for n in names))
source = (root/'PAFPlayer.py').read_text(encoding='utf-8')
tree = ast.parse(source)
compile(source, 'PAFPlayer.py', 'exec')
compile(Path(__file__).read_text(encoding='utf-8'), __file__, 'exec')
bundles = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '_PAF_BUNDLED_SOURCES':
                bundles.update(ast.literal_eval(node.value))
            if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == '_PAF_BUNDLED_SOURCES':
                bundles[ast.literal_eval(target.slice)] = ast.literal_eval(node.value)
for name, text in bundles.items():
    compile(text, name, 'exec')
    candidates = [root/'src'/(name+'.py'), root/'lockscreen/src'/(name+'.py'), root/'screensaver/src'/(name+'.py')]
    if name == 'PAFPlayer_lockscreen_installer':
        candidates.append(root/'lockscreen/lockscreen_installer.py')
    path = next(p for p in candidates if p.is_file())
    assert path.read_text(encoding='utf-8') == text, name
summary = dict(version=app.PROGRAM_VERSION, literal_cases=checks, surfaces=['plain/popup', 'console', 'web'],
               biggest_preserved=True, tests=result.testsRun, failures=[(str(c), t) for c,t in result.failures],
               errors=[(str(c), t) for c,t in result.errors], skipped=len(result.skipped),
               compiled=True, bundle_parity=len(bundles), blocked_writes=blocks,
               source_sha256=hashlib.sha256((root/'PAFPlayer.py').read_bytes()).hexdigest(), stage=str(stage))
with report.open('x', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2)); print(report)
sys.exit(0 if result.wasSuccessful() else 1)
