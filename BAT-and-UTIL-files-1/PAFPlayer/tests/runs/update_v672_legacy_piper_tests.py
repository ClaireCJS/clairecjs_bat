from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def update(p,pairs):
 s=p.read_text(encoding='utf8')
 for a,b in pairs:assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b,1)
 name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=p.with_name(name);i=0
 while backup.exists():i+=1;backup=p.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(p,backup);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
 p.write_text(s,encoding='utf8',newline='');dest=root/'backups'/backup.name;i=0
 while dest.exists():i+=1;dest=root/'backups'/(backup.stem+f' ({i})'+backup.suffix)
 shutil.move(str(backup),str(dest))
p=root/'tests/test_v657_dj_providers.py'
update(p,[("import importlib.util,io,json,os,threading,time,unittest", "import importlib.util,io,json,os,tempfile,threading,time,unittest"),
 ("  opts=d.settings({'piper_executable':'fake','piper_voices':'voice1\\nvoice2'});calls=[]", "  folder=Path(tempfile.mkdtemp(prefix='paf-legacy-voices-'));exe=folder/'piper';voice1=folder/'voice1';voice2=folder/'voice2'\n  for path in (exe,voice1,voice2):path.write_bytes(b'fixture')\n  opts=d.settings({'piper_executable':str(exe),'piper_voices':str(voice1)+'\\n'+str(voice2)});calls=[]"),
 ("self.assertEqual(['cloud','voice1','voice2'],calls)","self.assertEqual(['cloud',str(voice1),str(voice2)],calls)")])
p=root/'tests/test_v657_dj_cancel.py'
update(p,[("import importlib.util,io,threading,time,unittest", "import importlib.util,io,tempfile,threading,time,unittest"),
 ("  opts=d.settings({'speech_provider':'piper','piper_executable':'fake','piper_voices':'voice'})", "  folder=Path(tempfile.mkdtemp(prefix='paf-legacy-cancel-'));exe=folder/'piper';voice=folder/'voice'\n  for path in (exe,voice):path.write_bytes(b'fixture')\n  opts=d.settings({'speech_provider':'piper','piper_executable':str(exe),'piper_voices':str(voice)})")])
print('Updated legacy tests to use existing Piper fixture paths.')
