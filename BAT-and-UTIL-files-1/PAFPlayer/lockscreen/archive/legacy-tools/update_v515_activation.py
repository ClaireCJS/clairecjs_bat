from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for name in ('DesktopPackage.appxmanifest', 'DesktopHost.manifest', 'lockscreen_installer.py', 'build_desktop.ps1'):
    path = ROOT / 'lockscreen' / name
    value = path.read_text(encoding='utf-8').replace('515.0.0.0', '515.0.0.1')
    value = value.replace('PAFPlayerLockScreen_v515_x64.msix', 'PAFPlayerLockScreen_v515_1_x64.msix')
    path.write_text(value, encoding='utf-8')
path = ROOT / 'PAFPlayer.py'
rows = path.read_text(encoding='utf-8').splitlines(keepends=True)
index = next(i for i, line in enumerate(rows) if line.startswith('_PAF_BUNDLED_SOURCES["PAFPlayer_lockscreen"]'))
rows[index] = '_PAF_BUNDLED_SOURCES["PAFPlayer_lockscreen"] = ' + repr((ROOT / 'lockscreen/src/PAFPlayer_lockscreen.py').read_text(encoding='utf-8')) + '\n'
path.write_text(''.join(rows), encoding='utf-8')
