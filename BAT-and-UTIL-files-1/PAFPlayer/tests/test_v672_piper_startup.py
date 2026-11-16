import importlib.util,io,tempfile,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v672_dj',root/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)

class Tests(unittest.TestCase):
 def runtime(self):
  return SimpleNamespace(settings={'ai_dj':{'enabled':True}},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None,app=SimpleNamespace())
 def test_enabled_dj_prepares_free_models_in_background_once(self):
  runtime=self.runtime();called=threading.Event()
  def setup(stage,valid):called.set();return ('auto-piper','auto-voice')
  with mock.patch.object(dj,'ensure_piper',side_effect=setup) as install,mock.patch.object(dj,'ensure_piper_male',return_value='auto-male') as male,mock.patch.object(dj.shutil,'which',return_value=None):
   c=dj.get_controller(runtime);self.assertTrue(called.wait(2));deadline=time.monotonic()+2
   while c.piper_setup_running and time.monotonic()<deadline:time.sleep(.005)
   self.assertIs(c,dj.get_controller(runtime));self.assertEqual(1,install.call_count);male.assert_called_once()
   self.assertEqual('Free Piper voices are ready',c.piper_setup_stage)
 def test_missing_custom_paths_fall_back_to_auto_voice(self):
  opts=dj.settings({'speech_provider':'piper','piper_executable':'missing-executable','piper_voices':'missing-model','men':0})
  calls=[]
  def popen(args,**kwargs):
   calls.append(args);Path(args[args.index('-f')+1]).write_bytes(b'x'*100)
   return SimpleNamespace(stdin=io.BytesIO(),poll=lambda:0,returncode=0)
  with mock.patch.object(dj,'dialogue',return_value=([(1,'hello')],'')),mock.patch.object(dj.shutil,'which',return_value=None),mock.patch.object(dj,'ensure_piper',return_value=('auto-piper','auto-voice')),mock.patch.object(dj.subprocess,'Popen',side_effect=popen):
   files,warning=dj.synthesize([{'artist':'a','title':'b'}],opts,lambda _:None,lambda:True)
  self.assertEqual(1,len(files));self.assertEqual('auto-piper',calls[0][0]);self.assertEqual('auto-voice',calls[0][calls[0].index('-m')+1]);self.assertIn('paths were missing',warning)
 def test_detected_paths_and_missing_custom_are_visible(self):
  runtime=self.runtime();runtime.app=None;c=dj.Controller(runtime);c.configure({'piper_executable':'bad-exe','piper_voices':'bad-model'})
  with mock.patch.object(dj,'installed_piper',return_value=('detected-exe','female.onnx')),mock.patch.object(dj,'installed_piper_male',return_value='male.onnx'):
   status=c.status()
  self.assertEqual('detected-exe',status['piper_auto_executable']);self.assertEqual(['female.onnx','male.onnx'],status['piper_auto_voices']);self.assertEqual(['bad-exe','bad-model'],status['piper_missing_paths'])
 def test_failed_setup_can_be_retried(self):
  runtime=self.runtime();runtime.app=None;c=dj.Controller(runtime)
  with mock.patch.object(dj,'ensure_piper',side_effect=dj.PiperSetupError('offline')):
   self.assertTrue(c.start_piper_setup(force=True));deadline=time.monotonic()+2
   while c.piper_setup_running and time.monotonic()<deadline:time.sleep(.005)
  self.assertIn('failed',c.piper_setup_error)
  with mock.patch.object(dj,'ensure_piper',return_value=('exe','voice')),mock.patch.object(dj,'ensure_piper_male',return_value='male'):
   self.assertTrue(c.start_piper_setup(force=True));deadline=time.monotonic()+2
   while c.piper_setup_running and time.monotonic()<deadline:time.sleep(.005)
  self.assertEqual('',c.piper_setup_error);self.assertIn('ready',c.piper_setup_stage)
if __name__=='__main__':unittest.main()
