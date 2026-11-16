import importlib.util,sys,threading,tempfile,unittest,json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
spec=importlib.util.spec_from_file_location('candidate',str(Path(__file__).resolve().parents[1]/'PAFPlayer.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
import PAFPlayer_dj as dj
class Tests(unittest.TestCase):
 def setUp(self):
  dj.set_no_ai(False);self.root=Path(tempfile.mkdtemp());self.dcc=self.root/'PAFPlayer.dcc';self.dcc.write_text('{"other":"preserved"}')
  def read(path,default):
   try:return json.loads(path.read_text())
   except OSError:return default
  def write(path,value):path.write_text(json.dumps(value))
  self.app=SimpleNamespace(global_config_dcc_path=lambda:self.dcc,_global_config_read_json=read,_global_config_write_json=write,global_config_developer_choice_available=lambda:True)
  self.r=SimpleNamespace(settings={'ai_dj':{'seconds':60},'other':'keep'},lock=threading.RLock(),stop_event=threading.Event(),app=self.app,save_settings=mock.Mock())
  with mock.patch.object(dj.Controller,'start_piper_setup'):self.c=dj.get_controller(self.r)
 def test_named_and_factory_change_dj_only(self):
  dj.dj_profile_action(self.r,'save','Test');self.c.configure({'seconds':120});dj.dj_profile_action(self.r,'load','Test');self.assertEqual(60,self.c.options['seconds']);dj.dj_profile_action(self.r,'factory');self.assertEqual(90,self.c.options['seconds']);self.assertEqual('keep',self.r.settings['other'])
 def test_dcc_is_explicit_and_preserves_global_data(self):
  self.assertFalse(dj.dj_profiles_status(self.r)['dcc_available']);dj.dj_profile_action(self.r,'save_dcc');self.assertEqual('preserved',json.loads(self.dcc.read_text())['other']);self.c.configure({'seconds':125});dj.dj_profile_action(self.r,'load_dcc');self.assertEqual(60,self.c.options['seconds']);self.assertTrue(dj.dj_profiles_status(self.r)['dcc_available'])
 def test_profile_collision_is_refused(self):
  dj.dj_profile_action(self.r,'save','Test')
  with self.assertRaises(ValueError):dj.dj_profile_action(self.r,'save','Test')
 def test_race_restoration_is_reached_on_finish_and_cancel(self):
  import inspect
  src=inspect.getsource(m.play_audio_file)
  start=src.index('if paused_action is None and dj_started and dj_controller.play_done:')
  self.assertIn('restore_song_after_dj()',src[start:start+200]);self.assertIn('set_karaoke_timeline([])',src);self.assertIn('last_console_cue_key = None',src)
if __name__=='__main__':unittest.main()
