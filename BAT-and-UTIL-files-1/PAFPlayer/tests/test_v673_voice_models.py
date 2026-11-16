import importlib.util,json,sys,tempfile,unittest,wave
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v673_player',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_voice_models as models

class Tests(unittest.TestCase):
 def test_all_command_aliases_open_manager_without_starting_player(self):
  for flag in ('--dj','--models','--model','--install-models'):
   with self.subTest(flag=flag),mock.patch.object(p.subprocess,'Popen') as launch:
    self.assertEqual(0,p.main([flag]));self.assertIn('--models-window',launch.call_args.args[0])
  with mock.patch.object(p.subprocess,'Popen') as launch:
   self.assertEqual(2,p.main(['--models','song.mp3']));launch.assert_not_called()
  with mock.patch.object(models,'launch_window',return_value=0) as window:
   self.assertEqual(0,p.main(['--models-window']));window.assert_called_once_with()
 def test_first_install_can_open_model_window_and_continue(self):
  tty=SimpleNamespace(isatty=lambda:True);target=Path('installed-dir')
  with mock.patch.object(p,'paf_stage_self_install',return_value=target),mock.patch.object(p,'run_paf_readiness_check',return_value=0),mock.patch.object(p.sys,'stdin',tty),mock.patch('builtins.input',return_value='y'),mock.patch.object(p.subprocess,'Popen') as spawn:
   self.assertEqual(0,p.run_paf_self_install([],source=root/'PAFPlayer.py',base=root/'tests/runs',launch=True))
  self.assertEqual(2,spawn.call_count);self.assertIn('--models',spawn.call_args_list[0].args[0]);self.assertIn('--bootstrap-installed',spawn.call_args_list[1].args[0])
 def test_first_install_can_skip_model_setup(self):
  tty=SimpleNamespace(isatty=lambda:True);target=Path('installed-dir')
  with mock.patch.object(p,'paf_stage_self_install',return_value=target),mock.patch.object(p,'run_paf_readiness_check',return_value=0),mock.patch.object(p.sys,'stdin',tty),mock.patch('builtins.input',return_value=''),mock.patch.object(p.subprocess,'Popen') as spawn:
   self.assertEqual(0,p.run_paf_self_install([],source=root/'PAFPlayer.py',base=root/'tests/runs',launch=True))
  self.assertEqual(1,spawn.call_count);self.assertIn('--bootstrap-installed',spawn.call_args.args[0])
 def test_compare_creates_sample_files_and_records_timings(self):
  folder=Path(tempfile.mkdtemp(prefix='paf-model-test-'))
  def synth(model,text,gender,output,root=None,progress=None):
   with wave.open(str(output),'wb') as wav:wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(22050);wav.writeframes(b'\0\0'*100)
   return {'voice':gender,'duration_seconds':.01}
  with mock.patch.object(models,'installed',side_effect=lambda key,root=None:None if key=='qwen-small' else folder),mock.patch.object(models,'synthesize',side_effect=synth):
   dest,rows=models.compare(['piper','kokoro','qwen-small'],root=folder)
  self.assertEqual(5,len(rows));self.assertEqual('not installed',rows[-1]['status']);self.assertEqual(4,len(list(dest.glob('*.wav'))));self.assertEqual(rows,json.loads((dest/'results.json').read_text(encoding='utf8')))
  self.assertTrue(all('generation_seconds' in row for row in rows if row['status']=='ok'))
 def test_failed_model_does_not_stop_other_comparisons(self):
  folder=Path(tempfile.mkdtemp(prefix='paf-model-fail-'))
  with mock.patch.object(models,'installed',return_value=folder),mock.patch.object(models,'synthesize',side_effect=RuntimeError('sample failed')):
   dest,rows=models.compare(['kokoro','qwen-large'],root=folder)
  self.assertEqual(4,len(rows));self.assertTrue(all(row['status']=='error' for row in rows));self.assertTrue((dest/'results.json').is_file())
if __name__=='__main__':unittest.main()
