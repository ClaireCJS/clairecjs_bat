"""Apply V516 release labels to the already-backed-up working files."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
for name in ('DesktopHost.cs', 'DesktopHost.manifest', 'DesktopPackage.appxmanifest',
             'build_desktop.ps1', 'lockscreen_installer.py', 'run_regression_checks.py', 'test_desktop.ps1'):
    path = root / 'lockscreen' / name
    value = path.read_text(encoding='utf-8').replace('V515', 'V516').replace('v515', 'v516')
    value = value.replace('515.0.0.1', '516.0.0.0').replace('PAFPlayerLockScreen_v516_1_x64.msix', 'PAFPlayerLockScreen_v516_x64.msix')
    path.write_text(value, encoding='utf-8')
path = root / 'lockscreen/src/PAFPlayer_lockscreen.py'
value = path.read_text(encoding='utf-8').replace('PAFPlayer Lock Screen V515 for detailed', 'PAFPlayer Lock Screen V516 for detailed')
path.write_text(value, encoding='utf-8')
path = root / 'tests/test_v508_lockscreen_installer.py'
path.write_text(path.read_text(encoding='utf-8').replace('V515', 'V516'), encoding='utf-8')
path = root / 'PAFPlayer.py'
value = path.read_text(encoding='utf-8').replace('2026-10-08-v515-managed-lockscreen', '2026-10-08-v516-lockscreen-launch-environment')
value = re.sub(r'(?m)^(PROGRAM_(?:VERSION|RELEASE_LABEL)\s*=\s*)"V515"', r'\1"V516"', value)
rows = value.splitlines(keepends=True)
index = next(i for i, line in enumerate(rows) if line.startswith('_PAF_BUNDLED_SOURCES["PAFPlayer_lockscreen"]'))
rows[index] = '_PAF_BUNDLED_SOURCES["PAFPlayer_lockscreen"] = ' + repr((root / 'lockscreen/src/PAFPlayer_lockscreen.py').read_text(encoding='utf-8')) + '\n'
path.write_text(''.join(rows), encoding='utf-8')
