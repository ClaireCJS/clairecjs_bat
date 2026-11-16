import importlib.util,sys,threading,unittest
from pathlib import Path
from unittest import mock
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v675_piper_player',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_dj as dj
class Tests(unittest.TestCase):
 def test_piper_installer_forwards_output(self):
  lines=[];dj._PIPER_SETUP_PROGRESS.output=lines.append
  try:dj._piper_setup_command([sys.executable,'-u','-c',"print('Piper packages downloading',flush=True)"],root,lambda:True,timeout=10)
  finally:dj._PIPER_SETUP_PROGRESS.output=None
  self.assertIn('Piper packages downloading',lines)
 def test_piper_installer_honors_cancellation(self):
  with self.assertRaises(InterruptedError):dj._piper_setup_command([sys.executable,'-c','pass'],root,lambda:False,timeout=10)
if __name__=='__main__':unittest.main()
