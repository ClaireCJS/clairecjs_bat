from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('src/PAFPlayer_startup_cache.py','src/backups'),('PAFPlayer.py','releases')]:
 p=root/raw;base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest();dest=root/folder/b.name
 while dest.exists():n+=1;dest=root/folder/(base+f' ({n}).bak')
 b.rename(dest)
p=root/'src/PAFPlayer_startup_cache.py';s=p.read_text(encoding='utf-8');s=s.replace('import marshal\n','import marshal\nimport subprocess\nimport time\n',1)
start=s.index('        if candidate is None:');end=s.index('        bootstrap = (',start)
s=s[:start]+'''        if candidate is None:
            directory.mkdir(parents=True, exist_ok=True)
            recent = any(time.time() - marker.stat().st_mtime < 60 for marker in directory.glob('*.pending'))
            if not recent:
                marker = directory / (uuid.uuid4().hex + '.pending')
                with marker.open('x', encoding='utf-8') as stream: stream.write(str(time.time()))
                target = directory / (uuid.uuid4().hex + '.pyc')
                builder = (
                    "import sys,marshal,importlib.util;from pathlib import Path;"
                    "p=Path(sys.argv[1]);data=p.read_bytes();"
                    "payload=importlib.util.MAGIC_NUMBER+bytes(12)+marshal.dumps(compile(data,str(p),'exec'));"
                    "f=open(sys.argv[2],'xb');f.write(payload);f.close()"
                )
                subprocess.Popen([str(executable), '-B', '-c', builder, str(script), str(target)],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0))
            # Cache preparation must never delay the first audible preview.
            return fallback
'''+s[end:];p.write_text(s,encoding='utf-8')
p=root/'PAFPlayer.py';m=p.read_text(encoding='utf-8');lines=m.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  d=ast.literal_eval(line.split(' = ',1)[1]);d['PAFPlayer_startup_cache']=s;lines[i]='_PAF_BUNDLED_SOURCES = '+repr(d)+'\n'
m=''.join(lines);compile(m,str(p),'exec');p.write_text(m,encoding='utf-8')
