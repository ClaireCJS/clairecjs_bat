import importlib.util,sys,unittest,io,contextlib
from pathlib import Path
from unittest import mock
spec=importlib.util.spec_from_file_location('v683',str(Path(__file__).resolve().parents[1]/'PAFPlayer.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
import PAFPlayer_voice_models as v
class Tests(unittest.TestCase):
 def test_terminal_sequences_are_removed_even_when_streamed(self):
  seen=[]
  code="import sys;sys.stdout.write('\\x1b[?25l\\x1b[2Kpulling a5b03ec4: 2% | 1.1 GB/ 65 GB 118 MB/s 9m2s\\x1b[K\\r');sys.stdout.flush()"
  v.run_command([sys.executable,'-c',code],progress=seen.append)
  self.assertTrue(seen);self.assertIn('2%',seen[0]);self.assertNotIn('\x1b',seen[0]);self.assertNotIn('[?25l',seen[0])
 def test_launcher_returns_and_inherits_console(self):
  for flag in ('--dj','--models','--model','--install-models'):
   with self.subTest(flag=flag),mock.patch.object(m.subprocess,'Popen') as popen,contextlib.redirect_stdout(io.StringIO()) as out:
    self.assertEqual(0,m.main([flag]));self.assertIn('--models-window',popen.call_args.args[0]);self.assertFalse(popen.call_args.kwargs['close_fds']);self.assertIn('progress appears here',out.getvalue())
 def test_window_child_runs_manager(self):
  with mock.patch.object(v,'launch_window',return_value=0) as launch:self.assertEqual(0,m.main(['--models-window']));launch.assert_called_once()
if __name__=='__main__':unittest.main()
