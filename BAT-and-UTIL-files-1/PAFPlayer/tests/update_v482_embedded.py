"""One-time, checked mechanical update of the single-file bundled media sources."""
import ast
import hashlib
from datetime import datetime
from pathlib import Path
import shutil

path = Path(__file__).resolve().parents[1] / 'pafplayer.py'
original = path.read_bytes()
text = original.decode('utf-8-sig')
tree = ast.parse(text)
bundle = next(n.value for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == '_PAF_BUNDLED_SOURCES' for t in n.targets))
sources = ast.literal_eval(bundle)

def replace_once(source, old, new):
    assert source.count(old) == 1, old[:100]
    return source.replace(old, new, 1)

media = sources['PAFPlayer_windows_media']
media = replace_once(media, "'album':True,'timeline':True}", "'album':True,'timeline':True,'lyrics':False}")
media = replace_once(media, '\ndef presentation(state,options):', '''
def current_lyric(state, now=None):
    """Follow the shared timed cues, including blank gaps, offsets, seeks and pause."""
    timeline = state.get('lyric_timeline') or []
    if not timeline:
        return ' '.join(str(state.get('lyric') or '').split())
    now = time.time() if now is None else now
    position = float(state.get('lyric_position_seconds', 0) or 0)
    if state.get('playing') and not state.get('paused'):
        age = max(0.0, min(2.0, now - float(state.get('lyric_clock_epoch', now) or now)))
        position += age * float(state.get('speed', 1) or 1)
    position += float(state.get('karaoke_offset_seconds', 0) or 0)
    lyric = ''
    for start, cue in timeline:
        if float(start) > position:
            break
        lyric = str(cue or '')
    return ' '.join(lyric.split())


def presentation(state,options):''')
media = replace_once(media, "    return {'title':title,'artist':artist,", "    lyric = current_lyric(state) if options.get('lyrics') else ''\n    if lyric:\n        title += ' | ' + lyric\n    return {'title':title,'artist':artist,")
media = replace_once(media, "        if not server:return\n", "        if not server:\n            c.is_enabled=False;self.active=False\n            self.status={'state':'Waiting','reason':'Waiting for the player web-state publisher','title':'','brightness':None}\n            return\n")
media = replace_once(media, "        signature=(value['title'],value['artist'],value['album'],options['source'],options['artwork'],options['brightness'],getattr(self.runtime,'current_artwork_revision',0))", """        # A cue change must not resize/re-encode the same cover on every lyric.
        artwork_signature=((state.get('track') or {}).get('path'),state.get('art_generation'),state.get('art_count'),
                           options['source'],options['artwork'],options['brightness'],getattr(self.runtime,'current_artwork_revision',0))
        signature=(value['title'],value['artist'],value['album'],artwork_signature)""")
start = media.index('            data=artwork_bytes(self.runtime,options)')
end = media.index('            updater.update();self.signature=signature', start)
art = media[start:end]
media = media[:start] + "            if artwork_signature != getattr(self,'artwork_signature',None):\n" + ''.join('    ' + line + '\n' for line in art.splitlines()) + "                self.artwork_signature=artwork_signature\n" + media[end:]
media = replace_once(media, "                    self.stop.wait(1)", "                    self.stop.wait(0.2 if settings(self.runtime).get('lyrics') and self.active else 1.0)")
media = replace_once(media, "'Optional PyWinRT Windows.Media and Storage.Streams packages are not installed'", "'Missing Windows media dependencies; see docs/windows-lock-screen.md for the install command for this Python'")
ast.parse(media)
sources['PAFPlayer_windows_media'] = media
ui = sources['PAFPlayer_windows_ui']
ui = replace_once(ui, '<label><input type="checkbox" data-windows-setting="album" checked>', '<label title="Windows has no dedicated lyric field. Append the current timed line to the media title; Windows may truncate it. Music tags are unchanged."><input type="checkbox" data-windows-setting="lyrics">Include current lyric in Windows media title</label>\n<label><input type="checkbox" data-windows-setting="album" checked>')
ast.parse(ui)
sources['PAFPlayer_windows_ui'] = ui

# Replace only the two embedded literals; do not regenerate the enormous bundle
# or touch the old standalone modules (which the single-file app does not use).
lines = text.splitlines(keepends=True)
edits = []
for key, value in zip(bundle.keys, bundle.values):
    name = ast.literal_eval(key)
    if name in ('PAFPlayer_windows_media', 'PAFPlayer_windows_ui'):
        assert value.lineno == value.end_lineno
        edits.append((value.lineno - 1, value.col_offset, value.end_col_offset, repr(sources[name])))
for index, start, end, replacement in sorted(edits, reverse=True):
    # AST columns count UTF-8 bytes, not Unicode characters. Both literals can
    # share a single line, so apply ranges from right to left.
    line = lines[index].encode('utf-8')
    lines[index] = (line[:start] + replacement.encode('utf-8') + line[end:]).decode('utf-8')
updated = ''.join(lines)
updated = replace_once(updated, 'write_console("\\033[?7h" + move_to(0) + "\\033[?25h")', 'write_console(move_to(0) + "\\033[?7h\\033[?25h")')
ast.parse(updated)
assert path.read_bytes() == original, 'Source changed concurrently; no write performed'
backup = path.with_name(path.name + '.bak.' + datetime.now().strftime('%Y%m%d%H%M') + '.replaced-by-chatgpt.bak')
number = 1
while backup.exists():
    backup = backup.with_name(path.name + '.bak.' + datetime.now().strftime('%Y%m%d%H%M') + f'.replaced-by-chatgpt ({number}).bak')
    number += 1
shutil.copyfile(path, backup)
assert hashlib.sha256(backup.read_bytes()).digest() == hashlib.sha256(original).digest()
path.write_bytes(updated.encode('utf-8'))
print('Updated embedded Windows media/UI; verified backup:', backup)
