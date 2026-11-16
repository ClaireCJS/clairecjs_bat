import importlib.util,io,tempfile,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
p=Path(__file__).resolve().parents[1]/'src/PAFPlayer_dj.py';s=importlib.util.spec_from_file_location('dj_stop_test',p);d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
class Tests(unittest.TestCase):
 def test_cancel_terminates_local_synthesizer(self):
  calls=[];checks=[True,True,False]
  def valid():return checks.pop(0) if checks else False
  class P:
   stdin=io.BytesIO();returncode=None
   def poll(self):return self.returncode
   def terminate(self):calls.append('terminated');self.returncode=1
   def wait(self,timeout=None):return self.returncode
  folder=Path(tempfile.mkdtemp(prefix='paf-legacy-cancel-'));exe=folder/'piper';voice=folder/'voice'
  for path in (exe,voice):path.write_bytes(b'fixture')
  opts=d.settings({'speech_provider':'piper','piper_executable':str(exe),'piper_voices':str(voice)})
  with mock.patch.object(d,'dialogue',return_value=([(1,'test')],'')),mock.patch.object(d.subprocess,'Popen',return_value=P()):
   with self.assertRaises(InterruptedError):d.synthesize([{'artist':'a','title':'b'}],opts,lambda _:None,valid)
  self.assertEqual(['terminated'],calls)
 def test_failure_does_not_retry_next_track(self):
  runtime=SimpleNamespace(settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None);calls=[]
  def fail(*a):calls.append(1);raise RuntimeError('failure')
  c=d.Controller(runtime,fail);c.configure({'enabled':True});c.record('a','one')
  for _ in range(100):
   if c.working is None:break
   time.sleep(.005)
  c.record('b','two');self.assertEqual(1,len(calls));self.assertTrue(c.error)
 def test_force_can_use_current_played_track_without_history(self):
  runtime=SimpleNamespace(settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None);seen=[]
  c=d.Controller(runtime,lambda h,o,s,v:(seen.extend(h) or ['audio'],''));self.assertTrue(c.start(True,current={'artist':'a','title':'b'}))
  for _ in range(100):
   if c.working is None:break
   time.sleep(.005)
  self.assertEqual('b',seen[0]['title']);self.assertTrue(c.due())
if __name__=='__main__':unittest.main()
