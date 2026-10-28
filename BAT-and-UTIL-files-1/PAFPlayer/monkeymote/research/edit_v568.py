"""Release editing helpers: verify every replacement backup; never delete files."""
from pathlib import Path
from datetime import datetime
import hashlib

ROOT = Path(__file__).resolve().parents[2]

def unique(path):
    original = path
    i = 0
    while path.exists():
        i += 1
        path = original.with_name(f'{original.stem} ({i}){original.suffix}')
    return path

def write(path, text):
    path = ROOT / path
    data = text.encode('utf-8')
    if path.exists():
        old = path.read_bytes()
        if old == data:
            return
        folder = path.parent
        if path.name == 'PAFPlayer.py': folder = ROOT / 'releases'
        elif path.name == 'PAFPlayer_changelog.md': folder = ROOT / 'backups'
        elif path.suffix == '.md': folder = ROOT / 'docs'
        folder.mkdir(parents=True, exist_ok=True)
        backup = unique(folder / (path.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')))
        with backup.open('xb') as stream: stream.write(old)
        assert hashlib.sha256(old).digest() == hashlib.sha256(backup.read_bytes()).digest()
        assert path.read_bytes() == old, 'Concurrent modification; replacement stopped'
        print('BACKUP', backup)
    with path.open('wb' if path.exists() else 'xb') as stream: stream.write(data)
    assert path.read_bytes() == data
    print('WROTE', path)

def change(path, before, after):
    text = (ROOT / path).read_text(encoding='utf-8')
    assert text.count(before) == 1, (path, before[:100], text.count(before))
    write(path, text.replace(before, after, 1))
