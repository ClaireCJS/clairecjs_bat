import importlib.util,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v665_sleep_transition',ROOT/'src/PAFPlayer_dj.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class Tests(unittest.TestCase):
 def test_job_finishing_after_lock_is_discarded_and_can_retry_after_unlock(self):
  locked=[False];gate=threading.Event();started=threading.Event()
  app=SimpleNamespace(windows_session_is_locked=lambda:locked[0])
  runtime=SimpleNamespace(settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None,app=app)
  def producer(*args):started.set();gate.wait(2);return ['stale.wav'],''
  c=d.Controller(runtime,producer);c.configure({'sleep_when_locked':True,'enabled':True});c.history.append({'artist':'a','title':'b'});c.count=1;self.assertTrue(c.start(False));self.assertTrue(started.wait(1))
  locked[0]=True;c._sleep_cache_at=-1000;gate.set();deadline=time.monotonic()+2
  while c.working is not None and time.monotonic()<deadline:time.sleep(.005)
  self.assertIsNone(c.ready);self.assertFalse(c.forced);self.assertEqual('',c.stage);self.assertEqual(-1,c.attempted)
  locked[0]=False;c._sleep_cache_at=-1000;self.assertTrue(c.start(True,current={'artist':'a','title':'b'}))
if __name__=='__main__':unittest.main()
