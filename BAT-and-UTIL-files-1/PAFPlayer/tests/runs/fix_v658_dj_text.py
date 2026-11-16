from pathlib import Path
import datetime, hashlib, shutil

root = Path(__file__).resolve().parents[2]
src = root/'src/PAFPlayer_dj.py'
player = root/'PAFPlayer.py'
release = root/'releases/PAFPlayer_v658_dj_help_commentary.py'

def once(s, before, after):
    assert s.count(before) == 1, (before, s.count(before))
    return s.replace(before, after, 1)

dj = src.read_text(encoding='utf-8')
dj = once(dj, '    if not valid(): raise InterruptedError()\n    if on_dialogue is not None: on_dialogue(lines)', '    if on_dialogue is not None and valid(): on_dialogue(lines)')
dj = once(dj, '        def publish_dialogue(lines):\n            with self.lock:\n                if valid(): self.commentary=list(lines)', '        published=[]\n        def publish_dialogue(lines):\n            with self.lock:\n                if valid():\n                    self.commentary=list(lines);published.append(True)')
dj = once(dj, ' if self.commentary else \'DJ text generation failed;', ' if published else \'DJ text generation failed;')
body = player.read_text(encoding='utf-8').splitlines(keepends=True)
indices = [i for i, line in enumerate(body) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")]
assert len(indices) == 1
body[indices[0]] = "_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = " + repr(dj) + '\n'
text = ''.join(body)
compile(dj, str(src), 'exec'); compile(text, str(player), 'exec')
for path, data in ((src,dj),(player,text),(release,text)):
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')
    backup=path.with_name(name); i=0
    while backup.exists():
        i+=1;backup=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,backup)
    assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(data,encoding='utf-8',newline='')
    archive=root/('backups' if path==src else 'releases')/backup.name
    i=0
    while archive.exists():
        i+=1;archive=archive.with_name(backup.stem+f' ({i})'+backup.suffix)
    shutil.move(str(backup),str(archive))
print('Updated V658 cancellation behavior and kept bundle in sync.')
