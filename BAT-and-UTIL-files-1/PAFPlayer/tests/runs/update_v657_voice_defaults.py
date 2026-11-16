from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2];p=root/'tests/test_v657_dj.py';s=p.read_text(encoding='utf8')
a="self.assertEqual((10,0),(dj.settings({'speakers':10})['women'],dj.settings({'speakers':10})['men']))"
b="self.assertEqual((9,1),(dj.settings({'speakers':10})['women'],dj.settings({'speakers':10})['men']))"
assert s.count(a)==1
name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=p.with_name(name);i=0
while backup.exists():i+=1;backup=p.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(p,backup);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
p.write_text(s.replace(a,b,1),encoding='utf8',newline='');dest=root/'backups'/backup.name;i=0
while dest.exists():i+=1;dest=root/'backups'/(backup.stem+f' ({i})'+backup.suffix)
shutil.move(str(backup),str(dest));print('Updated voice-default regression expectation.')
