import importlib.util,io,json,os,tempfile,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
p=Path(__file__).resolve().parents[1]/'src/PAFPlayer_dj.py';sp=importlib.util.spec_from_file_location('dj_staged',p);d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
class R:
 def __init__(self):self.settings={};self.stop_event=threading.Event();self.lock=threading.RLock()
 def save_settings(self):pass
class ProviderTests(unittest.TestCase):
 def test_openai_text_failure_uses_ollama_without_secret(self):
  opts=d.settings({'ollama_model':'demo'});calls=[]
  def req(url,data,headers=None,timeout=None):
   calls.append(url)
   if 'openai' in url:raise RuntimeError('sensitive data')
   return {'message':{'content':'[{"speaker":1,"text":"hi"}]'}}
  with mock.patch.dict(os.environ,{'OPENAI_API_KEY':'example'}),mock.patch.object(d,'provider_key',return_value=''),mock.patch.object(d,'post_json',side_effect=req):
   rows,warning=d.dialogue([{'artist':'a','title':'b'}],opts)
  self.assertEqual([(1,'hi')],rows);self.assertEqual(2,len(calls));self.assertNotIn('sensitive',warning)
 def test_speech_failure_uses_piper_once_and_distinct_names(self):
  folder=Path(tempfile.mkdtemp(prefix='paf-legacy-voices-'));exe=folder/'piper';voice1=folder/'voice1';voice2=folder/'voice2'
  for path in (exe,voice1,voice2):path.write_bytes(b'fixture')
  opts=d.settings({'piper_executable':str(exe),'piper_voices':str(voice1)+'\n'+str(voice2)});calls=[]
  def cloud(*a):calls.append('cloud');raise RuntimeError('private')
  def run(args,**kw):
   output=Path(args[args.index('-f')+1]);
   with output.open('xb') as f:f.write(b'0'*100)
   calls.append(args[args.index('-m')+1]);return SimpleNamespace(returncode=0,stdin=io.BytesIO(),poll=lambda:0)
  with mock.patch.object(d,'dialogue',return_value=([(1,'a'),(2,'b')],'')),mock.patch.object(d,'speech_openai',side_effect=cloud),mock.patch.object(d.subprocess,'Popen',side_effect=run):
   files,warning=d.synthesize([{'artist':'x','title':'y'}],opts,lambda x:None,lambda:True)
  self.assertEqual(['cloud',str(voice1),str(voice2)],calls);self.assertEqual(2,len(set(files)));self.assertNotIn('private',warning)
 def test_cancel_before_speech(self):
  with mock.patch.object(d,'dialogue',return_value=([(1,'a')],'')),mock.patch.object(d,'speech_openai') as voice:
   with self.assertRaises(InterruptedError):d.synthesize([{'artist':'x','title':'y'}],d.settings(),lambda x:None,lambda:False)
   voice.assert_not_called()
 def test_settings_and_cancelled_jobs(self):
  self.assertEqual((7,3),tuple(d.settings({'speakers':10,'men':3})[k] for k in ('women','men')))
  gate=threading.Event();c=d.Controller(R(),lambda *args:(gate.wait(1) and ['x'],''));c.record('a','b',False);c.start(True);c.cancel_request();gate.set()
  for _ in range(100):
   if c.working is None:break
   time.sleep(.005)
  self.assertIsNone(c.ready)
 def test_force_does_not_duplicate_playback(self):
  c=d.Controller(R());c.play_thread=SimpleNamespace(is_alive=lambda:True)
  self.assertTrue(c.start(True));self.assertIsNone(c.working);self.assertFalse(c.forced)
if __name__=='__main__':unittest.main()
