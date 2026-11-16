"""Authenticate a supplied key and update private.env without printing it."""
from pathlib import Path
import datetime
import hashlib
import os
import re
import shutil
import sys
import urllib.error
import urllib.request

key=os.environ.pop('PAF_DJ_SETUP_KEY','').strip()
if not re.fullmatch(r'sk-[A-Za-z0-9_-]{20,}',key):
    print('Key handoff failed validation; no file was changed.');sys.exit(1)
request=urllib.request.Request('https://api.openai.com/v1/models',headers={'Authorization':'Bearer '+key})
try:
    with urllib.request.urlopen(request,timeout=20) as response:
        print('OpenAI authentication HTTP status:',response.status)
except urllib.error.HTTPError as exc:
    print('OpenAI authentication HTTP status:',exc.code,'; no file was changed.');sys.exit(1)
except Exception as exc:
    print('OpenAI authentication failed:',type(exc).__name__,'; no file was changed.');sys.exit(1)

path=Path(r'C:\BAT\private.env')
original=path.read_bytes()
pattern=re.compile(rb'(?m)^([ \t]*(?:export[ \t]+|set[ \t]+)?OPENAI_API_KEY[ \t]*=)[^\r\n]*')
if len(pattern.findall(original))!=1:
    print('Expected exactly one OPENAI_API_KEY assignment; no file was changed.');sys.exit(1)
updated=pattern.sub(lambda match:match.group(1)+key.encode('ascii'),original,count=1)
if updated==original:
    print('The verified key is already saved; no file was changed.');sys.exit(0)
name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')
backup=path.with_name(name);index=0
while True:
    try:
        with backup.open('xb') as target, path.open('rb') as source:
            shutil.copyfileobj(source,target)
        break
    except FileExistsError:
        index+=1;backup=path.with_name(name[:-4]+f' ({index}).bak')
shutil.copystat(path,backup)
if hashlib.sha256(original).digest()!=hashlib.sha256(backup.read_bytes()).digest():
    print('Backup verification failed; original was not changed. Backup created:',backup);sys.exit(1)
print('Created verified backup:',backup,flush=True)
with path.open('wb') as output: output.write(updated)
if path.read_bytes()!=updated:
    print('File verification failed; preserve and inspect backup:',backup);sys.exit(1)
print('Modified:',path)
