import importlib.util,io,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v673_install_player',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_voice_models as m

class Stream:
 def __enter__(self):self.stream=io.BytesIO(b'x'*12000);return self.stream
 def __exit__(self,*args):pass

class Tests(unittest.TestCase):
 def test_kokoro_download_installs_once_and_reuses_verified_files(self):
  base=Path(tempfile.mkdtemp(prefix='paf-kokoro-test-'));calls=[]
  def command(args,**kwargs):
   calls.append(args)
   if '-m' in args and 'venv' in args:
    py=m.python_in(kwargs['cwd']);py.parent.mkdir(parents=True);py.write_bytes(b'python')
  with mock.patch.object(m,'run_command',side_effect=command),mock.patch.object(m.urllib.request,'urlopen',side_effect=lambda *a,**k:Stream()) as download:
   folder=m.install('kokoro',root=base);self.assertEqual(folder,m.install('kokoro',root=base))
  self.assertEqual(2,download.call_count);self.assertEqual(2,len(calls));self.assertTrue((folder/'complete').is_file())
  self.assertTrue((folder/'kokoro-v1.0.onnx').is_file());self.assertTrue((folder/'voices-v1.0.bin').is_file())
 def test_failed_download_is_not_marked_installed(self):
  base=Path(tempfile.mkdtemp(prefix='paf-model-fail-'))
  def command(args,**kwargs):
   if 'venv' in args:
    py=m.python_in(kwargs['cwd']);py.parent.mkdir(parents=True);py.write_bytes(b'python')
  with mock.patch.object(m,'run_command',side_effect=command),mock.patch.object(m.urllib.request,'urlopen',side_effect=OSError('offline')):
   with self.assertRaises(OSError):m.install('kokoro',root=base)
  self.assertIsNone(m.installed('kokoro',base));self.assertEqual(1,len(list(base.iterdir())))
 def test_qwen_download_uses_the_requested_official_repository(self):
  base=Path(tempfile.mkdtemp(prefix='paf-qwen-test-'));calls=[]
  def command(args,**kwargs):
   calls.append([str(x) for x in args])
   if 'venv' in args:
    py=m.python_in(kwargs['cwd']);py.parent.mkdir(parents=True);py.write_bytes(b'python')
   elif '-c' in args:
    model=Path(args[-1]);model.mkdir();(model/'config.json').write_text('{}')
  with mock.patch.object(m,'run_command',side_effect=command):folder=m.install('qwen-small',root=base)
  self.assertTrue((folder/'complete').is_file());self.assertIn('Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice',calls[-1])
if __name__=='__main__':unittest.main()
