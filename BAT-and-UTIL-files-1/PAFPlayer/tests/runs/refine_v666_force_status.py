from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):
    assert s.count(a)==1;return s.replace(a,b,1)
def replace(p,data,archive):
    name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(name);i=0
    while b.exists():i+=1;b=p.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
    p.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
    while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
    if dest!=b:shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_dj.py';s=src.read_text(encoding='utf8')
s=once(s,"stage = ('Asleep: '+reason) if reason else ('Ready for next song' if self.ready and not self.forced else self.stage)","stage = ('Asleep: '+reason) if reason and not self.forced else ('Ready for next song' if self.ready and not self.forced else self.stage)")
s=once(s,'total, female=settings.get("female_speakers", total),\n        male=settings.get("male_speakers", 0), changed="total")','total, female=settings.get("female_speakers", total - (1 if total >= 2 else 0)),\n        male=settings.get("male_speakers", 1 if total >= 2 else 0), changed="total")')
compile(s,str(src),'exec');p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True)
idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(s)+'\n';text=''.join(lines);compile(text,str(p),'exec')
replace(src,s,root/'backups');replace(p,text,root/'releases');replace(root/'releases/PAFPlayer_v666_dj_force.py',text,root/'releases')
print('Updated forced-job help and default speaker profiles.')
