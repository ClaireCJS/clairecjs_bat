"""Authenticate supplied provider keys without printing or persisting them elsewhere."""
from pathlib import Path
import datetime,hashlib,json,re,shutil,sys,urllib.error,urllib.request

supplied=json.loads(sys.stdin.readline())
router=supplied.get('openrouter','').strip();gemini=supplied.get('gemini','').strip()
if not re.fullmatch(r'sk-or-v1-[A-Za-z0-9_-]{20,}',router) or not re.fullmatch(r'AQ\.[A-Za-z0-9_-]{20,}',gemini):
 print('Key handoff failed format validation; no file changed.');raise SystemExit(1)

def get_json(url,headers):
 request=urllib.request.Request(url,headers=headers)
 with urllib.request.urlopen(request,timeout=25) as response:return response.status,json.loads(response.read(2*1024*1024))

verified={}
try:
 status,data=get_json('https://openrouter.ai/api/v1/key',{'Authorization':'Bearer '+router})
 print('OpenRouter authentication HTTP:',status,'free-tier:',data.get('data',{}).get('is_free_tier'),flush=True)
 verified['OPENROUTER_API_KEY']=router
except urllib.error.HTTPError as e:print('OpenRouter authentication HTTP:',e.code,flush=True)
except Exception as e:print('OpenRouter authentication failed:',type(e).__name__,flush=True)
try:
 status,data=get_json('https://generativelanguage.googleapis.com/v1beta/models?pageSize=1',{'x-goog-api-key':gemini})
 print('Gemini authentication HTTP:',status,flush=True)
 verified['GEMINI_API_KEY']=gemini
except urllib.error.HTTPError as e:print('Gemini authentication HTTP:',e.code,flush=True)
except Exception as e:print('Gemini authentication failed:',type(e).__name__,flush=True)
if not verified:
 print('Neither key authenticated; no file changed.');raise SystemExit(1)

path=Path(r'C:\BAT\private.env');original=path.read_bytes();updated=original
for name,value in verified.items():
 pattern=re.compile(rb'(?m)^([ \t]*(?:export[ \t]+|set[ \t]+)?'+name.encode('ascii')+rb'[ \t]*=)[^\r\n]*')
 matches=list(pattern.finditer(updated))
 if len(matches)>1:raise SystemExit('Duplicate provider-key assignment; no file changed.')
 if matches:updated=pattern.sub(lambda m:m.group(1)+value.encode('ascii'),updated,count=1)
 else:
  if updated and not updated.endswith((b'\n',b'\r')):updated+=b'\r\n'
  updated+=name.encode('ascii')+b'='+value.encode('ascii')+b'\r\n'
if updated==original:
 print('Verified keys were already saved; no file changed.');raise SystemExit(0)
name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=path.with_name(name);i=0
while True:
 try:
  with backup.open('xb') as out,path.open('rb') as source:shutil.copyfileobj(source,out)
  break
 except FileExistsError:
  i+=1;backup=path.with_name(name[:-4]+f' ({i}).bak')
shutil.copystat(path,backup)
if hashlib.sha256(original).digest()!=hashlib.sha256(backup.read_bytes()).digest():
 print('Backup verification failed; original not changed. Backup created:',backup);raise SystemExit(1)
print('Created verified backup:',backup,flush=True)
with path.open('wb') as out:out.write(updated)
if path.read_bytes()!=updated:raise SystemExit('File verification failed; inspect the backup.')
print('Modified:',path,flush=True)
print('Saved provider names:',', '.join(verified),flush=True)
