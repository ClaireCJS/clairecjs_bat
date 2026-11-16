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
p=root/'PAFPlayer.py';s=p.read_text(encoding='utf8');a='section.append(heading,view);frame.appendChild(section);';b="section.append(heading,view);frame.insertBefore(section,document.getElementById('warningsSection'));";assert s.count(a)==1;s=s.replace(a,b,1);compile(s,str(p),'exec')
probe=root/'tests/runs/probe_v668_errors_tab.py';test=probe.read_text(encoding='utf8');a="==['Warnings','Errors']";b="==['Errors','Warnings']";assert test.count(a)==1;test=test.replace(a,b,1)
replace(p,s,root/'releases');replace(root/'releases/PAFPlayer_v668_playlist_errors.py',s,root/'releases');replace(probe,test,root/'backups')
print('Kept Warnings as the final configuration tab.')
