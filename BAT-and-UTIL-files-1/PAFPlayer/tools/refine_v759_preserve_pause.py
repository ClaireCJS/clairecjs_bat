from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('src/PAFPlayer_playback_focus.py','src/backups'),('PAFPlayer.py','releases')]:
 p=root/raw;base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest();dest=root/folder/b.name
 while dest.exists():n+=1;dest=root/folder/(base+f' ({n}).bak')
 b.rename(dest)
p=root/'src/PAFPlayer_playback_focus.py';s=p.read_text(encoding='utf-8')
needle='    def guard_action(self, action, paused, *, toggle='
idx=s.index(needle)
s=s[:idx]+'''    def begin_resume(self):
        """Commit resume intent atomically so a newly arriving preview must pause it."""
        with self.lock:
            if self.leases:
                return False
            self.resume_inflight = False
            self.paused[0] = False
            return True

'''+s[idx:];p.write_text(s,encoding='utf-8')
p=root/'PAFPlayer.py';m=p.read_text(encoding='utf-8');needle='''                        if paused_action == PAUSE_TOGGLE:
                            indicator = "▶️"'''
assert m.count(needle)==1;m=m.replace(needle,'''                        if paused_action == PAUSE_TOGGLE:
                            if playback_focus is not None and not playback_focus.begin_resume():
                                continue
                            indicator = "▶️"''',1)
lines=m.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  d=ast.literal_eval(line.split(' = ',1)[1]);d['PAFPlayer_playback_focus']=s;lines[i]='_PAF_BUNDLED_SOURCES = '+repr(d)+'\n'
m=''.join(lines);compile(m,str(p),'exec');p.write_text(m,encoding='utf-8')
