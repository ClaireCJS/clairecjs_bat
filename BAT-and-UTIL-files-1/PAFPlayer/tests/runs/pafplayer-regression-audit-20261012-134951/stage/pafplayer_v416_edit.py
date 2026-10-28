"""Task-local editing support: verified sibling backups for every replacement."""
from pathlib import Path
from datetime import datetime
import hashlib
import shutil

ROOT = Path(__file__).resolve().parent

def unique(path):
    path = Path(path)
    candidate = path
    n = 0
    while candidate.exists():
        n += 1
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
    return candidate

def replace_file(path, data):
    path = Path(path)
    data = data.encode('utf-8') if isinstance(data, str) else data
    if path.exists():
        original = path.read_bytes()
        if original == data:
            return
        backup = unique(path.with_name(path.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')))
        shutil.copy2(path, backup)
        assert hashlib.sha256(backup.read_bytes()).digest() == hashlib.sha256(original).digest()
        print(f'BACKUP {backup}')
    path.write_bytes(data)
    assert path.read_bytes() == data
    print(f'WROTE {path}')

def edit(transform):
    path = ROOT / 'play_audio_file.py'
    raw = path.read_bytes()
    source = raw.decode('utf-8').replace('\r\n', '\n')
    result = transform(source)
    compile(result, str(path), 'exec')
    replace_file(path, result.replace('\n', '\r\n') if b'\r\n' in raw else result)

def sub(source, old, new, count=1):
    found = source.count(old)
    assert found == count, (old[:120], found, count)
    return source.replace(old, new)
