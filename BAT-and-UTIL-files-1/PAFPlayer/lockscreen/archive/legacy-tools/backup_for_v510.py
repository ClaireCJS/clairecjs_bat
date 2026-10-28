"""Make verified backups before the V510 lock-screen source/release edits."""
from pathlib import Path
from datetime import datetime
import hashlib
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]

def backup(path):
    path = Path(path).resolve()
    path.relative_to(ROOT)
    folder = ROOT / 'releases' if path.name == 'PAFPlayer.py' else path.parent
    if path.suffix == '.md':
        folder = ROOT / 'docs'
    base = path.name + '.bak.' + datetime.now().strftime('%Y%m%d%H%M') + '.replaced-by-chatgpt'
    target = folder / (base + '.bak')
    n = 0
    while target.exists():
        n += 1
        target = folder / (base + f' ({n}).bak')
    with path.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst)
    if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(target.read_bytes()).digest():
        raise RuntimeError('Backup verification failed: ' + str(path))
    print(target)

if __name__ == '__main__':
    for name in sys.argv[1:]:
        backup(ROOT / name)
