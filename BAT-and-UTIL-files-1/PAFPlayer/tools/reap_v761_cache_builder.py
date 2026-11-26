from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('src/PAFPlayer_startup_cache.py','src/backups'),('PAFPlayer.py','releases')]:
 p=root/raw;base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest();dest=root/folder/b.name
 while dest.exists():n+=1;dest=root/folder/(base+f' ({n}).bak')
 b.rename(dest)
p=root/'src/PAFPlayer_startup_cache.py';s=p.read_text(encoding='utf-8').replace('import time\n','import time\nimport threading\n',1)
s=s.replace("                subprocess.Popen([str(executable), '-B', '-c', builder, str(script), str(target)],", "                process = subprocess.Popen([str(executable), '-B', '-c', builder, str(script), str(target)],",1)
needle="                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0))"
assert needle in s;s=s.replace(needle,needle+"\n                threading.Thread(target=process.wait, name='paf-code-cache-builder', daemon=True).start()",1);p.write_text(s,encoding='utf-8')
p=root/'PAFPlayer.py';m=p.read_text(encoding='utf-8');lines=m.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  d=ast.literal_eval(line.split(' = ',1)[1]);d['PAFPlayer_startup_cache']=s;lines[i]='_PAF_BUNDLED_SOURCES = '+repr(d)+'\n'
m=''.join(lines);compile(m,str(p),'exec');p.write_text(m,encoding='utf-8')
