"""Exercise real local synthesis after a simulated exhausted OpenAI balance."""
import io,json,sys,tempfile,threading,time,urllib.error,wave
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'src'))
import PAFPlayer_dj as d
test_root=Path(tempfile.mkdtemp(prefix='v662-live-local-',dir=str(root/'tests/runs')))
r=SimpleNamespace(root=test_root,settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None)
original=d.post_json
def post(url,data,headers=None,timeout=45):
 if url.startswith('https://api.openai.com/'):
  raise urllib.error.HTTPError(url,429,'',{},io.BytesIO(b'{"error":{"code":"credit_balance_exhausted"}}'))
 return original(url,data,headers,timeout)
def no_cloud_speech(*args):raise RuntimeError('Cloud speech deliberately mocked')
with mock.patch.object(d,'post_json',side_effect=post),mock.patch.object(d,'speech_openai',side_effect=no_cloud_speech),mock.patch.object(d,'provider_key',return_value=''):
 c=d.Controller(r);c.configure({'enabled':True,'seconds':15});c.start(True,current={'artist':'Example Artist','title':'Example Song'})
 deadline=time.monotonic()+240;last=''
 while c.working is not None and time.monotonic()<deadline:
  status=c.status()
  if status['stage']!=last:last=status['stage'];print('Stage:',last,flush=True)
  time.sleep(1)
 status=c.status();print('Ready:',status['ready'],'Warning present:',bool(status['warnings']),'Working:',status['working'],flush=True)
 if not c.ready or not status['warnings']:raise SystemExit('Probe did not produce a ready segment and warning')
 for path in c.ready:
  with wave.open(path,'rb') as wav:
   if wav.getnframes()<=0:raise SystemExit('Empty WAV')
 print('Verified WAV files:',len(c.ready),flush=True)
