"""Run every embedded player test in preserved staging, with live-write guards."""
from pathlib import Path
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def child(stage):
    for key in ('TEMP', 'TMP', 'LOCALAPPDATA', 'APPDATA'):
        os.environ[key] = str(stage)
    os.environ['PLAY_AUDIO_FILE_HISTORY_DB'] = str(stage / 'history.sqlite3')
    for key in tuple(os.environ):
        if key.startswith('LASTFM_') or key == 'PAFPLAYER_DISCORD_WEBHOOK':
            os.environ.pop(key)
    tempfile.tempdir = str(stage)
    sys.path.insert(0, str(ROOT))
    from run_PAFPlayer_tests import install_guards
    sys.path.insert(0, str(stage))
    os.chdir(stage)
    install_guards(stage)
    # Compact mismatched ANSI frames without weakening equality assertions.
    def compact_diff(left, right, *args, **kwargs):
        import itertools
        for index, (a, b) in enumerate(itertools.zip_longest(left, right)):
            if a != b:
                yield 'First differing line: ' + str(index)
                yield '- ' + str(a)[:1200]
                yield '+ ' + str(b)[:1200]
                return
    unittest.case.difflib.ndiff = compact_diff
    import PAFPlayer
    suite = unittest.defaultTestLoader.loadTestsFromModule(PAFPlayer)
    result = unittest.TextTestRunner(verbosity=1, stream=sys.stdout).run(suite)
    print(json.dumps({'tests': result.testsRun, 'failures': len(result.failures),
                      'errors': len(result.errors), 'skips': len(result.skipped)}))
    return 0 if result.wasSuccessful() else 1


def main():
    stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    stage = ROOT / 'lockscreen' / ('embedded-staging-' + stamp)
    stage.mkdir()
    shutil.copyfile(ROOT / 'PAFPlayer.py', stage / 'PAFPlayer.py')
    report = ROOT / 'tests/reports' / ('v515-embedded-' + stamp + '.txt')
    with report.open('xb') as stream:
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()), '--child', str(stage)],
                                stdout=stream, stderr=subprocess.STDOUT, timeout=600)
    print('Report:', report)
    print(report.read_text(encoding='utf-8')[-5000:])
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(child(Path(sys.argv[2])) if len(sys.argv) > 1 else main())
