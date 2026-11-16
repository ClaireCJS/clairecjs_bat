"""Exercise both free text providers with actual local Piper speech."""
import sys,time,wave
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'src'))
import PAFPlayer_dj as d
for provider in ('openrouter','gemini'):
 events=[];d._DJ_THREAD_CONTEXT.log=lambda name,**fields:events.append((name,fields))
 opts=d.settings({'text_provider':provider,'speech_provider':'piper','gemini_free_confirmed':True,'seconds':15})
 start=time.monotonic()
 try:
  files,warning=d.synthesize([{'artist':'Example Artist','title':'Example Song'}],opts,lambda _:None,lambda:True)
  if not any(name=='text.provider.success' and data.get('provider')==provider for name,data in events):
   print(provider,'did not generate text; fallback:',warning,flush=True);raise SystemExit(1)
  for path in files:
   with wave.open(path,'rb') as audio:
    if audio.getnframes()<=0:raise SystemExit('Empty audio')
  print(provider,'generated',len(files),'valid WAV files in',round(time.monotonic()-start,1),'seconds',flush=True)
 finally:d._DJ_THREAD_CONTEXT.log=None
