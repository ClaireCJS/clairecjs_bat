import unittest
from dj_scheduler import Scheduler,Settings,validate_settings
class SchedulerTests(unittest.TestCase):
 def test_schedule_and_force(self):
  d=Scheduler(Settings(enabled=True));d.played('Metallica','One')
  token,history,_=d.begin();self.assertEqual('One',history[0]['title']);self.assertIsNone(d.begin(True));self.assertTrue(d.finish(token,'audio'))
  self.assertEqual('audio',d.take());self.assertIsNone(d.take())
 def test_due_and_stale(self):
  d=Scheduler(Settings(enabled=True));d.played('A','B'); token,_,_=d.begin();d.played('C','D');d.finish(token,'x');self.assertEqual('x',d.take())
  d.played('A','B');token,_,_=d.begin();d.cancel();self.assertFalse(d.finish(token,'old'));self.assertIsNone(d.take())
 def test_fail_no_retry_and_settings(self):
  d=Scheduler(Settings(enabled=True));d.played('A','B');token,_,_=d.begin();d.finish(token,error='failed');self.assertEqual('failed',d.error)
  s=validate_settings({'speakers':10,'men':3},'men');self.assertEqual((10,7,3),(s.speakers,s.women,s.men))
  s=validate_settings({'speakers':10,'women':8,'men':3},'women');self.assertEqual((8,2),(s.women,s.men))
if __name__=='__main__':unittest.main()
