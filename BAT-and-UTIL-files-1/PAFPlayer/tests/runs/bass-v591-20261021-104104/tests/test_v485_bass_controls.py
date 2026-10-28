import sys,unittest
from pathlib import Path
from unittest import mock
sys.dont_write_bytecode=True
import probe_v482_track_renderer as probe
p=probe.app
class BassControls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.local,cls.ns=probe.capture_renderer(170,47)
 def test_inactive_controls_do_not_restart(self):
  s=dict(p.PLAYER_SETTING_DEFAULTS)
  s.update(BassBoostEnabled=0,BassBoostPercent=0,ReduceBassWhenLocked=0,LockedBassReductionPercent=50)
  ns=self.ns
  with mock.patch.dict(ns,load_bass_settings=lambda:dict(s),save_player_setting_value=lambda k,v:s.__setitem__(k,v),windows_session_is_locked=lambda:False):
   apply=self.local['apply_web_direct_setting']
   for key,value in [('reduce_bass_when_locked',1),('locked_bass_reduction_percent',80),('bass_boost_percent',50),('reduce_bass_when_locked',0)]:
    self.assertEqual((True,False),apply(f'web-set:{key}:{value}',100.))
   self.assertEqual((True,True),apply('web-set:bass_boost_enabled:1',100.))
   self.assertEqual((True,False),apply('web-set:bass_boost_enabled:1',100.))
 def test_audible_change_updates_monitor_identity(self):
  s=dict(p.PLAYER_SETTING_DEFAULTS)
  s.update(BassBoostEnabled=0,BassBoostPercent=0,ReduceBassWhenLocked=0,LockedBassReductionPercent=50)
  with mock.patch.dict(self.ns,load_bass_settings=lambda:dict(s),save_player_setting_value=lambda k,v:s.__setitem__(k,v),windows_session_is_locked=lambda:True):
   apply=self.local['apply_web_direct_setting']
   self.assertEqual((True,True),apply('web-set:reduce_bass_when_locked:1',100.))
   cells=dict(zip(apply.__code__.co_freevars,apply.__closure__))
   self.assertEqual(-10.,cells['last_bass_filter_signature'].cell_contents)
   self.assertEqual(-10.,p.bass_settings_effective_db(s,locked=True))
   self.assertEqual((True,False),apply('web-set:reduce_bass_when_locked:1',100.))
   self.assertEqual(0.,p.bass_settings_effective_db(s,locked=False))
if __name__=='__main__':unittest.main()
