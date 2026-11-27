from __future__ import annotations

import datetime
import hashlib
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
releases = root / "releases"
old_release = releases / "PAFPlayer_v763_circled_number_spacing.py"
old_backup = releases / "PAFPlayer_v763_circled_number_spacing.py.bak.202611270848.replaced-by-chatgpt (1).bak"
new_release = releases / "PAFPlayer_v764_circled_number_single_gap.py"
if not old_backup.is_file():
    raise FileNotFoundError(old_backup)
if new_release.exists():
    raise FileExistsError(new_release)


def backup(path: Path) -> Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    base = path.name + f".bak.{stamp}.replaced-by-chatgpt"
    target = path.with_name(base + ".bak")
    i = 0
    while target.exists():
        i += 1
        target = path.with_name(base + f" ({i}).bak")
    shutil.copy2(path, target)
    original_hash = hashlib.sha256(path.read_bytes()).digest()
    if hashlib.sha256(target.read_bytes()).digest() != original_hash:
        raise RuntimeError(f"Backup verification failed: {target}")
    return target


preserved = backup(old_release)
old_hash = hashlib.sha256(old_backup.read_bytes()).digest()
shutil.copy2(old_backup, old_release)
if hashlib.sha256(old_release.read_bytes()).digest() != old_hash:
    raise RuntimeError("Could not restore V763 release from verified pre-V764 backup")

active = root / "PAFPlayer.py"
shutil.copy2(active, new_release)
if hashlib.sha256(active.read_bytes()).digest() != hashlib.sha256(new_release.read_bytes()).digest():
    raise RuntimeError("V764 release does not match active source")

print("BACKUP", preserved)
print("RESTORED V763", old_release)
print("CREATED V764", new_release)
print("SHA256", hashlib.sha256(new_release.read_bytes()).hexdigest())
