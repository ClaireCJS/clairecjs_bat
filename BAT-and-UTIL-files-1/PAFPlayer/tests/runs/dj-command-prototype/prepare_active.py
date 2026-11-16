from pathlib import Path
from datetime import datetime
import ast, hashlib, shutil
root=Path(__file__).resolve().parents[2]
p=root/'PAFPlayer.py'
original=p.read_bytes(); text=original.decode('utf-8')
prototype=(Path(__file__).parent/'command_entry.py').read_text(encoding='utf-8-sig')
prototype=prototype.replace('class CommandEntry:', 'class PAFHashCommandEntry:', 1)
anchor='def read_windows_key_action(rename_editor: InlineRenameEditor | None = None) -> str | None:'
assert text.count(anchor)==1
text=text.replace(anchor, prototype+'\n\n_HASH_COMMAND_ENTRY = PAFHashCommandEntry()\n_HASH_COMMAND_PREFIX = "hash-command:"\n\n\n'+anchor,1)
needle='''    import msvcrt

    if _GLOBAL_SEEK_CAPTURE is not None:
'''
replacement='''    import msvcrt

    # Commands own buffered console input until Enter, Escape, or an idle
    # timeout. Polling stays nonblocking, including in the paused loop.
    command_entry = _HASH_COMMAND_ENTRY
    if command_entry.buffer is not None:
        command = command_entry.expire(time.monotonic())
        if command is not None:
            return _HASH_COMMAND_PREFIX + command
        if command_entry.buffer is not None:
            if not msvcrt.kbhit():
                return None
            char = msvcrt.getwch()
            if char in ("\\x00", "\\xe0"):
                if msvcrt.kbhit():
                    msvcrt.getwch()
                return None
            _, command = command_entry.feed(char, time.monotonic())
            return _HASH_COMMAND_PREFIX + command if command else None

    if _GLOBAL_SEEK_CAPTURE is not None:
'''
assert text.count(needle)==1
text=text.replace(needle,replacement,1)
needle='''    first = msvcrt.getwch()
    char_deadline = _ASYNC_CHAR_SUPPRESS_ONCE.get(first)
'''
replacement='''    first = msvcrt.getwch()
    if first == "#" and not (rename_editor is not None and rename_editor.active):
        _HASH_COMMAND_ENTRY.feed(first, time.monotonic())
        return None
    char_deadline = _ASYNC_CHAR_SUPPRESS_ONCE.get(first)
'''
assert text.count(needle)==1
text=text.replace(needle,replacement,1)
needle='''                if action_value in tone_actions:
'''
replacement='''                if isinstance(action_value, str) and action_value.startswith(_HASH_COMMAND_PREFIX):
                    command = action_value[len(_HASH_COMMAND_PREFIX):]
                    set_transient_notice("Unknown command: #" + command, seconds=3.0)
                    return None
                if action_value in tone_actions:
'''
assert text.count(needle)==1
text=text.replace(needle,replacement,1)
for name in ('PROGRAM_VERSION', 'PROGRAM_RELEASE_LABEL'):
    old=f"{name}{' ' * (31-len(name))}= 'V655'"
    new=old.replace('V655','V656')
    assert text.count(old)==1, repr(old)
    text=text.replace(old,new,1)
ast.parse(text); compile(text,str(p),'exec')
assert p.read_bytes()==original, 'Source changed during preparation'
backup=p.with_name(p.name+datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak'))
i=0
while backup.exists():
    i+=1; backup=p.with_name(p.name+datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt')+f' ({i}).bak')
with backup.open('xb') as f: f.write(original)
assert hashlib.sha256(backup.read_bytes()).digest()==hashlib.sha256(original).digest()
assert p.read_bytes()==original
p.write_bytes(text.encode('utf-8'))
archive=root/'releases'/backup.name
assert not archive.exists()
backup.rename(archive)
print('updated',p,'backup',archive)
