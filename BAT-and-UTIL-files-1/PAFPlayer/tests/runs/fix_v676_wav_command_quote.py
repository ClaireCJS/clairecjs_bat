from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2];p=root/'src/PAFPlayer_wav_menu.py';s=p.read_text(encoding='utf8')
a="    return subprocess.list2cmdline([python,'-B',script,'--enqueue-or-play','%1'])";b="    return subprocess.list2cmdline([python,'-B',script,'--enqueue-or-play'])+' \"%1\"'";assert s.count(a)==1
name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=p.with_name(name);i=0
while backup.exists():i+=1;backup=p.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(p,backup);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
p.write_text(s.replace(a,b,1),encoding='utf8',newline='');dest=root/'backups'/backup.name;i=0
while dest.exists():i+=1;dest=root/'backups'/(backup.stem+f' ({i})'+backup.suffix)
shutil.move(str(backup),str(dest));print('Quoted Explorer file argument.')
