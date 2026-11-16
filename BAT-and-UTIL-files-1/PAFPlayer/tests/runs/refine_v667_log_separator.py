from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def replace(p,data,archive):
    name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(name);i=0
    while b.exists():i+=1;b=p.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
    p.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
    while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
    if dest!=b:shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_dj.py';s=src.read_text(encoding='utf8');a="output = ['', '━━━━━━━━━━━━━━━━━━━━━━',";b="output = ['━━━━━━━━━━━━━━━━━━━━━━',";assert s.count(a)==1;s=s.replace(a,b,1)
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1;lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(s)+'\n';text=''.join(lines);compile(s,str(src),'exec');compile(text,str(p),'exec')
replace(src,s,root/'backups');replace(p,text,root/'releases');replace(root/'releases/PAFPlayer_v667_dj_conversation_log.py',text,root/'releases')
print('Aligned each entry with the requested separator.')
