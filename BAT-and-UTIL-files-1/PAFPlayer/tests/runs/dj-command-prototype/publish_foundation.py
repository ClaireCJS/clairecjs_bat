from pathlib import Path
from datetime import datetime
import hashlib
root=Path(__file__).resolve().parents[3]
def write(relative,text,archive):
 p=root/relative; original=p.read_bytes(); data=text.encode('utf8')
 backup=p.with_name(p.name+datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')); base=backup; n=0
 while backup.exists() or (root/archive/backup.name).exists():
  n+=1; backup=base.with_name(f'{base.stem} ({n}){base.suffix}')
 with backup.open('xb') as f:f.write(original)
 assert hashlib.sha256(backup.read_bytes()).digest()==hashlib.sha256(original).digest()
 assert p.read_bytes()==original
 p.write_bytes(data); assert p.read_bytes()==data
 backup.rename(root/archive/backup.name)
 print('updated',p)
p=root/'docs/README.md'; s=p.read_text(encoding='utf8')
old='Current release: **V655** — smoother, configurable, boundary-safe idle artwork motion.\n[Controls, beat behavior, limitations, and verification](../releases/PAFPlayer_v655_idle_behavior_motion_release_notes.md).'
new='Current release: **V656** — nonblocking console command-entry foundation.\n[Release notes and current limitations](../releases/PAFPlayer_v656_hash_command_foundation_release_notes.md).'
assert s.count(old)==1
s=s.replace(old,new,1)
s=s.replace('## Start and configure\n','## Console command entry\n\nDuring playback or pause, type `#` followed by a command, then press Enter or wait 1.5 seconds. Backspace edits and Escape cancels. The command entry is a foundation only: no DJ commands or AI podcaster are implemented yet.\n\n## Start and configure\n',1)
write('docs/README.md',s,'docs')
p=root/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf8');header='# PAFPlayer changelog\n\n';assert s.startswith(header)
s=header+'''## V656 — November 11, 2026

Add nonblocking, editable, timeout-based console command entry during playback
and pause. This is a foundation only: AI DJ commands and commentary are not yet
implemented. [Release notes](../releases/PAFPlayer_v656_hash_command_foundation_release_notes.md).

'''+s[len(header):]
write('docs/PAFPlayer_changelog.md',s,'backups')
source=(root/'PAFPlayer.py').read_bytes(); dest=root/'releases/PAFPlayer_v656_hash_command_foundation.py'
with dest.open('xb') as f:f.write(source)
assert dest.read_bytes()==source
notes=root/'releases/PAFPlayer_v656_hash_command_foundation_release_notes.md'
with notes.open('x',encoding='utf8',newline='\n') as f:f.write('''# PAFPlayer V656 — command-entry foundation

Adds a nonblocking `#` console command entry shared by the playing and paused
input loops. Enter submits, Backspace edits, Escape cancels, and 1.5 seconds
of inactivity submits. Unrecognized commands display a notice. The existing
Ctrl+Alt+D binding is unchanged.

This is an incomplete step toward the requested AI DJ: `#dj` and `#djforce`
are not implemented, and neither are synthesis, playback coordination, provider
fallback, or settings. No AI network requests are made by this version.

Five focused tests pass; the player and its 27 embedded modules compile and all
27 embedded sources match their editable counterparts. Live console interaction
has not been verified. No literal C:\\BAT path was changed.
''')
print('created',dest,notes)
