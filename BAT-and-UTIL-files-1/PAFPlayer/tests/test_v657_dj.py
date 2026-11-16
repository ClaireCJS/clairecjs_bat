import importlib.util,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('dj',Path(__file__).resolve().parents[1]/'src/PAFPlayer_dj.py');dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)
class Runtime:
 def __init__(self):self.settings={};self.stop_event=threading.Event();self.lock=threading.RLock();self.saves=0
 def save_settings(self):self.saves+=1
class DJTests(unittest.TestCase):
 def test_balancing(self):
  self.assertEqual((9,1),(dj.settings({'speakers':10})['women'],dj.settings({'speakers':10})['men']))
  self.assertEqual((7,3),tuple(dj.settings({'speakers':10,'men':3})[k] for k in ('women','men')))
  self.assertEqual((4,6),tuple(dj.settings({'speakers':10,'women':4,'men':1},'women')[k] for k in ('women','men')))
  with self.assertRaises(ValueError):dj.settings({'speakers':0})
 def test_preparation_due_and_forced(self):
  r=Runtime();gate=threading.Event()
  def produce(h,o,s,v):gate.wait(1);return ['audio'],''
  c=dj.Controller(r,produce);c.configure({'enabled':True});c.record('a','one');self.assertTrue(c.working)
  c.start(True);self.assertTrue(c.status()['stage']);gate.set()
  for _ in range(100):
   if c.ready:break
   time.sleep(.005)
  self.assertTrue(c.due());self.assertEqual(['audio'],c.take());self.assertFalse(c.due())
 def test_generation_cancel_discards_result(self):
  r=Runtime();gate=threading.Event();c=dj.Controller(r,lambda *args:(gate.wait(1) and ['stale'],''))
  c.record('a','b');c.start(True);self.assertTrue(c.working);c.cancel_request();gate.set()
  for _ in range(100):
   if c.working is None:break
   time.sleep(.005)
  self.assertIsNone(c.ready);self.assertFalse(c.forced)
 def test_failure_has_no_busy_loop_retry(self):
  r=Runtime();calls=[]
  def fail(*x):calls.append(1);raise RuntimeError('secret')
  c=dj.Controller(r,fail);c.configure({'enabled':True});c.record('a','b')
  for _ in range(100):
   if c.working is None:break
   time.sleep(.005)
  for _ in range(10):c.start()
  self.assertEqual(1,len(calls));self.assertNotIn('secret',c.error)
 def test_parse_and_untrusted_fields(self):
  self.assertEqual([(1,'hello')],dj.parse_dialogue('[{"speaker":1,"text":"hello"}]',2))
  with self.assertRaises(ValueError):dj.parse_dialogue('[{"speaker":3,"text":"x"}]',2)
  self.assertNotIn(':',dj.safe_name('a:b','c/d',1))
if __name__=='__main__':unittest.main()
