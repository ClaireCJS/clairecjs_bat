import importlib.util,json,tempfile,threading,time,unittest
from datetime import datetime,date,timezone,timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dj_sleep_candidate',ROOT/'src/PAFPlayer_dj.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class Tests(unittest.TestCase):
 def runtime(self,app=None):return SimpleNamespace(root=Path(tempfile.mkdtemp(prefix='dj-sleep-test-')),settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None,app=app)
 def test_defaults_and_validation(self):
  opts=d.settings();self.assertEqual(('never','sunrise','22312',False),tuple(opts[k] for k in ('sleep_time','wake_time','sunrise_zip','sleep_when_locked')))
  for values in ({'sunrise_zip':'abcde'},{'sleep_time':'25:00'},{'sleep_time':'02:00','wake_time':'02:00'},{'sleep_when_locked':1}):
   with self.assertRaises(ValueError):d.settings(values)
 def test_fixed_hours_cross_midnight_and_same_day(self):
  tz=timezone(timedelta(hours=-5));night=d.settings({'sleep_time':'23:00','wake_time':'07:00'})
  for h,want in [(22,False),(23,True),(0,True),(6,True),(7,False),(14,False)]:
   self.assertEqual(want,bool(d.sleep_evaluation(night,datetime(2026,11,12,h,0,tzinfo=tz),False,None)[0]))
  day=d.settings({'sleep_time':'01:00','wake_time':'08:00'})
  for h,want in [(0,False),(1,True),(7,True),(8,False),(23,False)]:
   self.assertEqual(want,bool(d.sleep_evaluation(day,datetime(2026,11,12,h,0,tzinfo=tz),False,None)[0]))
 def test_sunrise_default_and_missing_zip_fallback_are_visible(self):
  tz=timezone(timedelta(hours=-5));m=d.sunrise_minutes(date(2026,11,12),38.8191,-77.1484,tz)
  self.assertTrue(6*60+35<m<7*60)
  opts=d.settings({'sleep_time':'00:00'})
  self.assertTrue(d.sleep_evaluation(opts,datetime(2026,11,12,6,0,tzinfo=tz),False,d.DEFAULT_ZIP_COORDINATES['22312'])[0])
  self.assertFalse(d.sleep_evaluation(opts,datetime(2026,11,12,8,0,tzinfo=tz),False,d.DEFAULT_ZIP_COORDINATES['22312'])[0])
  reason,note=d.sleep_evaluation(opts,datetime(2026,11,12,6,0,tzinfo=tz),False,None)
  self.assertTrue(reason);self.assertIn('7:00 AM',note)
 def test_locked_blocks_force_and_unlock_clears_sleep_error(self):
  locked=[True];app=SimpleNamespace(windows_session_is_locked=lambda:locked[0]);c=d.Controller(self.runtime(app),lambda *a:(['wav'],''));c.configure({'sleep_when_locked':True})
  self.assertFalse(c.start(False,current={'artist':'a','title':'b'}));self.assertIn('asleep',c.error)
  self.assertIn('screen locked',c.help_snapshot()[1]);locked[0]=False;c._sleep_cache_at=-1000
  self.assertTrue(c.start(True,current={'artist':'a','title':'b'}));self.assertNotIn('asleep',c.error)
 def test_audio_terminates_when_screen_locks(self):
  locked=[False];app=SimpleNamespace(windows_session_is_locked=lambda:locked[0]);c=d.Controller(self.runtime(app));c.configure({'sleep_when_locked':True});started=threading.Event();terminated=threading.Event()
  class Process:
   def poll(self):return 0 if terminated.is_set() else None
   def terminate(self):terminated.set()
  def spawn(*args,**kwargs):started.set();return Process()
  with mock.patch.object(d.subprocess,'Popen',side_effect=spawn):
   self.assertTrue(c.play(['dummy.wav'],'ffplay'));self.assertTrue(started.wait(1));locked[0]=True;c._sleep_cache_at=-1000
   self.assertTrue(terminated.wait(2));c.play_thread.join(2)
  self.assertTrue(c.play_done)
 def test_zip_lookup_runs_in_background_and_is_cached(self):
  r=self.runtime();location=d.SunriseLocation(r)
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,*args):return json.dumps({'places':[{'latitude':'40.7','longitude':'-74.0'}]}).encode()
  with mock.patch.object(d.urllib.request,'urlopen',return_value=Response()) as request:
   self.assertIsNone(location.get('10001'))
   deadline=time.monotonic()+2
   while '10001' in location.active and time.monotonic()<deadline:time.sleep(.005)
   self.assertEqual((40.7,-74.0),location.get('10001'));self.assertEqual(1,request.call_count)
  location2=d.SunriseLocation(r);self.assertEqual((40.7,-74.0),location2.get('10001'))
if __name__=='__main__':unittest.main()
