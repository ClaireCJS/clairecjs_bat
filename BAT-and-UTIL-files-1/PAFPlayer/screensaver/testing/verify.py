"""Run sidecar and affected player checks in preserved, isolated directories."""
from datetime import datetime
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys

TESTING = Path(__file__).resolve().parent
SIDE = TESTING.parent
ROOT = SIDE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SIDE / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
os.chdir(ROOT)
from build_PAFPlayer_screensaver import build
import run_PAFPlayer_tests as runner

output = TESTING / 'old' / ('verification-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
output.mkdir(exist_ok=False)
executable = build(SIDE, output / 'PAFPlayer.scr')
compiler = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
subprocess.run([str(compiler), '/nologo', '/target:exe', '/platform:x64', '/main:SaverTests',
                '/out:' + str(output / 'tests.exe'), '/reference:System.Windows.Forms.dll',
                '/reference:System.Drawing.dll', '/reference:System.Web.Extensions.dll',
                str(SIDE / 'src' / 'PAFPlayer_screensaver.cs'), str(TESTING / 'test_PAFPlayer_screensaver.cs')],
               check=True, creationflags=subprocess.CREATE_NO_WINDOW)
native = subprocess.run([str(output / 'tests.exe'), str(output), str(executable)], capture_output=True,
                        text=True, encoding='utf-8', errors='replace', timeout=45,
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
with (output / 'native-results.txt').open('x', encoding='utf-8') as stream:
    stream.write(native.stdout + '\n' + native.stderr)
print(native.stdout, flush=True)
if native.returncode: print(native.stderr); raise SystemExit(native.returncode)

audit, stage, discovered = runner.prepare()
print('Python audit: ' + str(audit), flush=True)
modules = ['test_PAFPlayer_screensaver', 'test_PAFPlayer_v458', 'test_PAFPlayer_v459',
           'test_PAFPlayer_v456', 'test_PAFPlayer_v456_release', 'test_PAFPlayer_workflows']
reports = []
for module in modules:
    assert module in discovered, 'Test discovery lost ' + module
    result_path = audit / (module + '.json')
    with (audit / (module + '.log')).open('xb') as log:
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT / 'tests' / 'run_PAFPlayer_tests.py'),
                                 '--child', str(stage), module, str(result_path)], stdout=log, stderr=subprocess.STDOUT,
                                timeout=120, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    report = json.loads(result_path.read_text())
    reports.append(report)
    print(module, report.get('count'), report.get('successful'), flush=True)
    for entry in report.get('entries', []):
        if entry['outcome'] != 'pass': print(entry)

summary = {'audit': str(audit), 'native_checks': int(re.search(r'COMPLETE: (\d+) checks passed', native.stdout).group(1)), 'python_tests': sum(r['count'] for r in reports),
           'successful': all(r['successful'] for r in reports), 'modules': modules,
           'player_sha256': hashlib.sha256((stage / 'PAFPlayer.py').read_bytes()).hexdigest(),
           'screensaver_sha256': hashlib.sha256(executable.read_bytes()).hexdigest()}
with (output / 'results.json').open('x', encoding='utf-8') as stream: json.dump(reports, stream, indent=2)
with (output / 'summary.json').open('x', encoding='utf-8') as stream: json.dump(summary, stream, indent=2)
print(json.dumps(summary, indent=2), flush=True)
raise SystemExit(0 if summary['successful'] else 1)
