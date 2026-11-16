from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2];path=root/'tests/test_v657_dj_providers.py';s=path.read_text(encoding='utf8')
old="  with mock.patch.dict(os.environ,{'OPENAI_API_KEY':'example'}),mock.patch.object(d,'post_json',side_effect=req):"
new="  with mock.patch.dict(os.environ,{'OPENAI_API_KEY':'example'}),mock.patch.object(d,'provider_key',return_value=''),mock.patch.object(d,'post_json',side_effect=req):"
assert s.count(old)==1;s=s.replace(old,new,1)
name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=path.with_name(name);i=0
while b.exists():i+=1;b=path.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(path,b);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
path.write_text(s,encoding='utf8',newline='');dest=root/'backups'/b.name;i=0
while dest.exists():i+=1;dest=root/'backups'/(b.stem+f' ({i})'+b.suffix)
shutil.move(str(b),str(dest));print('Isolated provider fallback test from real user credentials.')
