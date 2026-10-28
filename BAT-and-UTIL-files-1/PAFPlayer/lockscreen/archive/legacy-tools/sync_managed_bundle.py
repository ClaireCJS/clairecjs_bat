"""Update the application bundle after making and verifying its required backup."""
from pathlib import Path
from backup_for_v510 import backup

root = Path(__file__).resolve().parents[1]
path = root / 'PAFPlayer.py'
backup(path)
rows = path.read_text(encoding='utf-8').splitlines(keepends=True)
index = next(i for i, line in enumerate(rows) if line.startswith('_PAF_BUNDLED_SOURCES["PAFPlayer_lockscreen"]'))
rows[index] = '_PAF_BUNDLED_SOURCES["PAFPlayer_lockscreen"] = ' + repr((root / 'lockscreen/src/PAFPlayer_lockscreen.py').read_text(encoding='utf-8')) + '\n'
path.write_text(''.join(rows), encoding='utf-8')
