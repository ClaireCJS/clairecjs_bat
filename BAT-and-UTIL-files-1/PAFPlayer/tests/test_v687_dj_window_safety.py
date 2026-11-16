import importlib.util,sys,threading,unittest,tempfile,contextlib,io
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
spec=importlib.util.spec_from_file_location('v687',str(Path(__file__).resolve().parents[1]/'PAFPlayer.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
import PAFPlayer_dj as d
import PAFPlayer_remote_tray as tray
class Tests(unittest.TestCase):
 def tearDown(self):d.set_no_ai(False)
 def test_disabled_ai_blocks_manual_start_and_setup_without_changing_settings(self):
  r=SimpleNamespace(settings={'ai_dj':{'enabled':True}},lock=threading.RLock(),stop_event=threading.Event(),save_settings=mock.Mock())
  d.set_no_ai(True);c=d.get_controller(r);self.assertFalse(c.options['enabled']);self.assertFalse(c.start(True,current={'artist':'a','title':'b'}));self.assertFalse(c.start_piper_setup());c.configure({'enabled':True});r.save_settings.assert_not_called();self.assertTrue(r.settings['ai_dj']['enabled'])
 def test_aliases_select_correct_placement(self):
  for flag in ('--enqueue','--queue','--en'):
   with self.subTest(flag=flag),mock.patch.object(tray,'run_enqueue',return_value=0) as e:self.assertEqual(0,m.main([flag,'x.m3u']));e.assert_called_once_with(['x.m3u'],placement='after_current')
  for flag in ('--enqueue-at-end','--queue-at-end'):
   with self.subTest(flag=flag),mock.patch.object(tray,'run_enqueue',return_value=0) as e:self.assertEqual(0,m.main([flag,'x.m3u']));e.assert_called_once_with(['x.m3u'],placement='end')
 def test_noai_rejects_model_window(self):
  with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(2,m.main(['--noai','--models']))
 def test_playlist_relaunch_waits_for_child(self):
  folder=Path(tempfile.mkdtemp());path=folder/'x.m3u';path.write_text('#EXTM3U')
  with mock.patch.object(m.subprocess,'call',return_value=7) as call:self.assertEqual(7,m.relaunch_pafplayer_with_playlist(path));self.assertIn(str(path),call.call_args.args[0])
 def test_pause_artwork_only_suppressed_for_competing_sound(self):
  self.assertTrue(m.visualizer_track_artwork_allowed(5,True));self.assertFalse(m.visualizer_track_artwork_allowed(5,True,True))
 def test_piper_windows_process_detached(self):
  with mock.patch.object(d.os,'name','nt'),mock.patch.object(d.subprocess,'STARTUPINFO') as si,mock.patch.object(d.subprocess,'DETACHED_PROCESS',8,create=True),mock.patch.object(d.subprocess,'CREATE_NEW_PROCESS_GROUP',512,create=True),mock.patch.object(d.subprocess,'STARTF_USESHOWWINDOW',1,create=True):
   si.return_value.dwFlags=0;opts=d.piper_process_options();self.assertEqual(520,opts['creationflags']);self.assertEqual(0,opts['startupinfo'].wShowWindow)
if __name__=='__main__':unittest.main()
