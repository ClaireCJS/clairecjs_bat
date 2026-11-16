import os, sys, tempfile, threading, time
from pathlib import Path
from types import SimpleNamespace

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'src'))
import PAFPlayer_dj as dj

test_root=Path(tempfile.mkdtemp(prefix='v660-real-job-',dir=str(root/'tests/runs')))
runtime=SimpleNamespace(root=test_root,settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None)
c=dj.Controller(runtime)
c.configure({'enabled':True,'text_provider':'ollama','speech_provider':'piper','seconds':90})
print('Diagnostic file:',c.log.path,flush=True)
c.start(True,current={'artist':'Example Artist','title':'Example Song'})
deadline=time.monotonic()+240
last=''
while c.working is not None and time.monotonic()<deadline:
    s=c.status()
    if s['stage']!=last:
        last=s['stage'];print('Stage:',last,flush=True)
    time.sleep(1)
s=c.status()
print('Result:',{k:s[k] for k in ('stage','error','ready','working','log_available')},flush=True)
if c.ready:
    import wave
    for path in c.ready:
        with wave.open(path,'rb') as wav:
            if wav.getnframes()<=0:raise SystemExit('Empty WAV')
    print('Verified speech files:',len(c.ready),flush=True)
else:raise SystemExit(1)
