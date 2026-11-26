from pathlib import Path
import datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('PAFPlayer.py','releases'),('docs/README.md','docs/backups'),('docs/PAFPlayer_changelog.md','docs/backups')]:
 p=root/raw;base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest()
 target=root/folder/b.name;target.parent.mkdir(exist_ok=True,parents=True)
 while target.exists():n+=1;target=root/folder/(base+f' ({n}).bak')
 b.rename(target)
p=root/'PAFPlayer.py';s=p.read_text(encoding='utf-8-sig');s=s.replace("= 'V759'","= 'V760'").replace('2026-11-25-v759-preserve-main-pause','2026-11-25-v760-erase-after-interrupt')
old='        print("\\n⏹️ Playback stopped.")';new='        print("\\n⏹️ Playback stopped.\\033[J", flush=True)'
assert s.count(old)==1;s=s.replace(old,new,1);compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
p=root/'docs/README.md';s=p.read_text(encoding='utf-8-sig');s+='\n\n### V760: Ctrl+C cleanup below the stop message\n\nAfter printing `Playback stopped.`, the Ctrl+C handler emits ANSI erase-to-end-of-screen (`ESC[J`) before its newline and flushes the output. This clears leftover karaoke/progress content below the message while preserving text above it and the existing simple-mode terminal behavior.\n';p.write_text(s,encoding='utf-8')
p=root/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf-8-sig');s=s.replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V760 — November 25, 2026\n\nErase from the end of the Ctrl+C Playback stopped message to the bottom of the screen, clearing leftover karaoke/progress content. [Release notes](../releases/PAFPlayer_v760_erase_after_interrupt_release_notes.md).\n',1);p.write_text(s,encoding='utf-8')
print('V760 Ctrl+C cleanup applied with verified backups.')
