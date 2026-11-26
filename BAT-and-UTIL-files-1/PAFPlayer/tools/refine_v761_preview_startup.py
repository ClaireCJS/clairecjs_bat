from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('src/PAFPlayer_startup_cache.py','src/backups'),('PAFPlayer.py','releases')]:
 p=root/raw;base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest();dest=root/folder/b.name
 while dest.exists():n+=1;dest=root/folder/(base+f' ({n}).bak')
 b.rename(dest)
p=root/'src/PAFPlayer_startup_cache.py';s=p.read_text(encoding='utf-8-sig');s=s.replace('else:exec(code,{\'__name__\':\'__main__\',\'__file__\':source,\'__package__\':None})\\n','else:\\n import __main__;g=vars(__main__);g.update(__file__=source,__package__=None);exec(code,g)\\n');p.write_text(s,encoding='utf-8')
p=root/'PAFPlayer.py';m=p.read_text(encoding='utf-8-sig');m=m.replace("if result.returncode == 0 and isinstance(payload, dict)","if getattr(result, 'returncode', 0) == 0 and isinstance(payload, dict)",1);m=m.replace('        if result.returncode != 0:\n            analysis_succeeded',"        if getattr(result, 'returncode', 0) != 0:\n            analysis_succeeded",1)
lines=m.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  d=ast.literal_eval(line.split(' = ',1)[1]);d['PAFPlayer_startup_cache']=s;lines[i]='_PAF_BUNDLED_SOURCES = '+repr(d)+'\n'
m=''.join(lines);compile(m,str(p),'exec');p.write_text(m,encoding='utf-8')
