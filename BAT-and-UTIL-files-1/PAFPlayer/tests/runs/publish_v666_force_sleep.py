from pathlib import Path
import datetime, hashlib, shutil

root = Path(__file__).resolve().parents[2]
def once(s, old, new):
    assert s.count(old) == 1, (old[:100], s.count(old))
    return s.replace(old, new, 1)
def replace(path, data, archive):
    original = path.read_bytes()
    name = path.name + datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')
    backup = path.with_name(name); i = 0
    while backup.exists():
        i += 1; backup = path.with_name(name[:-4] + f' ({i}).bak')
    shutil.copy2(path, backup)
    assert hashlib.sha256(original).digest() == hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(data, encoding='utf8', newline='')
    destination = archive / backup.name; i = 0
    while destination != backup and destination.exists():
        i += 1; destination = archive / (backup.stem + f' ({i})' + backup.suffix)
    if destination != backup: shutil.move(str(backup), str(destination))

src = root/'src/PAFPlayer_dj.py'; dj = src.read_text(encoding='utf8')
dj = once(dj, 'speakers=2, women=2, men=0,', 'speakers=2, women=1, men=1,')
dj = once(dj, "voices='marin,coral,cedar,sage,shimmer,alloy,ash,ballad,echo,verse'", "voices='marin,cedar,coral,sage,shimmer,alloy,ash,ballad,echo,verse'")
dj = once(dj, 'self.play_thread=None;self.play_process=None;self.play_cancel=threading.Event();self.play_done=False', 'self.play_thread=None;self.play_process=None;self.play_cancel=threading.Event();self.play_done=False;self.play_forced=False')
dj = once(dj, "            if reason:\n                self.forced=False;self.error='AI DJ is asleep: '+reason", "            if reason and not forced:\n                self.forced=False;self.error='AI DJ is asleep: '+reason")
dj = once(dj, "            if self.play_thread and self.play_thread.is_alive():\n                self.log.write('job.skipped', reason='playing', forced=bool(forced));return True", "            if self.play_thread and self.play_thread.is_alive():\n                if forced:self.play_forced=True\n                self.log.write('job.skipped', reason='playing', forced=bool(forced));return True")
dj = once(dj, 'and not self.sleep_status()[0]\n        def stage(message):', 'and (self.forced or not self.sleep_status()[0])\n        def stage(message):')
dj = once(dj, 'if token==self.serial and self.sleep_status()[0]:', 'if token==self.serial and not self.forced and self.sleep_status()[0]:')
dj = once(dj, "with self.lock:return bool(not self.sleep_status()[0] and self.ready and (self.forced or (self.options['enabled'] and self.count>=self.options['interval'])))", "with self.lock:return bool(self.ready and (self.forced or (not self.sleep_status()[0] and self.options['enabled'] and self.count>=self.options['interval'])))")
dj = once(dj, "result=self.ready;self.ready=None;self.forced=False;self.count=0;self.stage='';self.log.write('job.taken', audio_files=len(result));return result", "result=self.ready;self.ready=None;self.play_forced=self.forced;self.forced=False;self.count=0;self.stage='';self.log.write('job.taken', audio_files=len(result));return result")
dj = once(dj, 'if self.play_cancel.wait(.1) or self.sleep_status()[0]:', 'if self.play_cancel.wait(.1) or (not self.play_forced and self.sleep_status()[0]):')
dj = once(dj, 'self.play_process=None;self.play_done=True', 'self.play_process=None;self.play_done=True;self.play_forced=False')
dj = once(dj, '"target_seconds": 90, "speaker_count": 2, "female_speakers": 2,\n    "male_speakers": 0,', '"target_seconds": 90, "speaker_count": 2, "female_speakers": 1,\n    "male_speakers": 1,')
compile(dj, str(src), 'exec')
player = root/'PAFPlayer.py'; lines = player.read_text(encoding='utf8').splitlines(keepends=True)
indices = [i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")]
assert len(indices)==1; lines[indices[0]] = "_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = " + repr(dj) + '\n'
text=''.join(lines)
text=once(text, "'2026-11-12-v665-dj-sleep'", "'2026-11-12-v666-dj-force'")
text=once(text, "PROGRAM_VERSION                = 'V665'", "PROGRAM_VERSION                = 'V666'")
text=once(text, "PROGRAM_RELEASE_LABEL          = 'V665'", "PROGRAM_RELEASE_LABEL          = 'V666'")
compile(text,str(player),'exec')
release=root/'releases/PAFPlayer_v666_dj_force.py'; notes=root/'releases/PAFPlayer_v666_dj_force_release_notes.md'
assert not release.exists() and not notes.exists()
readme=root/'docs/README.md'; documentation=readme.read_text(encoding='utf8')
documentation=once(documentation, 'Current release: **V665** — DJ sleep hours and screen-lock sleep.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v665_dj_sleep_release_notes.md).', 'Current release: **V666** — forced DJ overrides sleep; default cast is one woman and one man.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v666_dj_force_release_notes.md).')
documentation=once(documentation, 'When asleep, new DJ jobs—including `#djforce`—do not start, prepared segments wait, and active DJ speech stops.', 'When asleep, automatic DJ jobs do not start, prepared automatic segments wait, and active automatic speech stops. `#djforce` overrides both scheduled and screen-lock sleep for that request.')
documentation=once(documentation, 'speaker counts (two women by default)', 'speaker counts (one woman and one man by default; previously saved choices are preserved)')
documentation=once(documentation, 'Gender is a requested cast, not a guaranteed characteristic of the provider’s voices.', 'Gender is a requested cast, not a guaranteed characteristic of the provider’s voices. Piper uses the configured voice models; its automatic installation currently provides one voice, so configure two Piper voice models for distinct local voices.')
changelog=root/'docs/PAFPlayer_changelog.md'; change=changelog.read_text(encoding='utf8')
change=once(change, '# PAFPlayer changelog\n', '# PAFPlayer changelog\n\n## V666 — November 12, 2026\n\nAllow `#djforce` through scheduled and lock-screen sleep, including generation and playback; default to one woman and one man. [Release notes](../releases/PAFPlayer_v666_dj_force_release_notes.md).\n')
replace(src,dj,root/'backups'); replace(player,text,root/'releases'); release.write_text(text,encoding='utf8',newline='')
replace(readme,documentation,root/'docs'); replace(changelog,change,root/'backups')
notes.write_text('# PAFPlayer V666 — Force DJ through sleep\n\n`#djforce` overrides scheduled and lock-screen sleep through generation and playback. Automatic commentary still sleeps. New default casts contain one woman and one man; existing saved selections are preserved. The automatic Piper installation currently includes one voice model; configure two models for distinct local voices.\n',encoding='utf8')
print('Published workspace V666 with verified backups.')
