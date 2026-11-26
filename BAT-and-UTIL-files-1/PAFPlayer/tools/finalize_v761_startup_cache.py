from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('tests/test_v761_startup_cache.py','tests/backups'),('src/PAFPlayer_startup_cache.py','src/backups'),('PAFPlayer.py','releases')]:
 p=root/raw;base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest();dest=root/folder/b.name
 while dest.exists():n+=1;dest=root/folder/(base+f' ({n}).bak')
 b.rename(dest)
p=root/'tests/test_v761_startup_cache.py';s=p.read_text(encoding='utf-8-sig').replace("self.assertFalse(list((self.cache.root/'silence').glob('*/*.json'))))","self.assertFalse(list((self.cache.root/'silence').glob('*/*.json')))");p.write_text(s,encoding='utf-8')
p=root/'src/PAFPlayer_startup_cache.py';s=p.read_text(encoding='utf-8');s=s.replace('"f=open(sys.argv[2],\'xb\');f.write(payload);f.close()"','"target=Path(sys.argv[2]);temp=target.with_suffix(\'.building\');"\n                    "f=open(temp,\'xb\');f.write(payload);f.close();temp.rename(target)"');p.write_text(s,encoding='utf-8')
p=root/'PAFPlayer.py';m=p.read_text(encoding='utf-8');lines=m.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  d=ast.literal_eval(line.split(' = ',1)[1]);d['PAFPlayer_startup_cache']=s;lines[i]='_PAF_BUNDLED_SOURCES = '+repr(d)+'\n'
m=''.join(lines);compile(m,str(p),'exec');p.write_text(m,encoding='utf-8')
