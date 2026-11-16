from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def replace(path,data,archive):
 name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=path.with_name(name);i=0
 while b.exists():i+=1;b=path.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(path,b);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 path.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
 while dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
 shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_dj.py';dj=src.read_text(encoding='utf8')
old='''                with self.lock:
                    if self.working==token:self.working=None
'''
new='''                with self.lock:
                    if self.working==token:
                        self.working=None
                        if token==self.serial and self.sleep_status()[0]:
                            self.forced=False;self.stage='';self.attempted=-1
'''
assert dj.count(old)==1;dj=dj.replace(old,new,1)
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n';text=''.join(lines);compile(dj,'dj','exec');compile(text,str(p),'exec')
replace(src,dj,root/'backups');replace(p,text,root/'releases');replace(root/'releases/PAFPlayer_v665_dj_sleep.py',text,root/'releases')
print('Reset interrupted DJ generation state when sleep begins.')
