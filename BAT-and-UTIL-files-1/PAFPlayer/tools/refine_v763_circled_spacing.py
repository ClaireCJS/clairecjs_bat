from __future__ import annotations

import datetime
import hashlib
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def verified_backup(path: Path) -> Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    stem = path.name + f".bak.{stamp}.replaced-by-chatgpt"
    backup = path.with_name(stem + ".bak")
    i = 0
    while backup.exists():
        i += 1
        backup = path.with_name(stem + f" ({i}).bak")
    shutil.copy2(path, backup)
    digest = hashlib.sha256(path.read_bytes()).digest()
    if hashlib.sha256(backup.read_bytes()).digest() != digest:
        raise RuntimeError(f"Backup verification failed: {backup}")
    return backup


main = root / "PAFPlayer.py"
release = root / "releases" / "PAFPlayer_v763_circled_number_spacing.py"
for path in (main, release):
    print("BACKUP", verified_backup(path))

old = '''    """Add terminal-only safety cells after generated enclosed-number forms.

    Windows Terminal's DECDHL renderer can visually consume the first safety
    cell after a negative circled digit.  Existing one-digit behavior remains
    unchanged.  V390 additionally recognizes a tens compound such as ``❹⓿``
    as one visual number, keeps those two digits adjacent, and appends the two
    safety cells only after the pair.  Web/Tk/other-terminal surfaces never
    call this compatibility helper, so they keep the exact replacement with no
    artificial trailing cells. V398 also gives the ``write`` substitution one
    terminal-only safety cell: Windows Terminal can paint ✍ beyond the advance
    it reports, despite the following source-space cell being present.
    """
    pattern = re.compile(
        rf"(?:[{re.escape(WINDOWS_TERMINAL_SPACED_EMOJIMAX_GLYPHS)}]⓿|"
        rf"[{re.escape(WINDOWS_TERMINAL_SPACED_EMOJIMAX_GLYPHS)}])"
    )'''
new = '''    """Preserve lyric text while applying the few remaining glyph workarounds.

    Circled-number substitutions are returned unchanged: their original lyric
    whitespace already provides the intended separation. The separate safety
    cell for the ``write`` substitution remains for Windows Terminal.
    """'''
data = main.read_text(encoding="utf-8-sig")
if data.count(old) != 1:
    raise RuntimeError("Expected helper docstring and obsolete pattern exactly once")
main.write_text(data.replace(old, new), encoding="utf-8", newline="")
shutil.copy2(main, release)
if hashlib.sha256(main.read_bytes()).digest() != hashlib.sha256(release.read_bytes()).digest():
    raise RuntimeError("Release does not match active source")
print("UPDATED", main)
print("UPDATED", release)
