"""Compare the previous immutable release using exactly the V515 test harness."""
from pathlib import Path
import datetime
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
stage = root / 'lockscreen' / ('baseline-staging-' + stamp)
stage.mkdir()
shutil.copyfile(root / 'releases/PAFPlayer_v514_lockscreen_background_registration.py', stage / 'PAFPlayer.py')
report = root / 'tests/reports' / ('v515-baseline-v514-' + stamp + '.txt')
with report.open('xb') as stream:
    result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(root / 'lockscreen/run_embedded_v515.py'), '--child', str(stage)],
                            stdout=stream, stderr=subprocess.STDOUT, timeout=600)
print('Baseline report:', report)
print(report.read_text(encoding='utf-8')[-260:])
raise SystemExit(result.returncode)
