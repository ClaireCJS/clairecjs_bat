import importlib.util, threading,time,unittest,wave,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("djtest",str(Path(__file__).resolve().parents[1] / "src" / "PAFPlayer_dj.py"));dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)
class Process:
 def __init__(self,cmd,**kwargs):self.cmd=cmd;self.live=True
 def poll(self):return None if self.live else 0
 def terminate(self):self.live=False
 def kill(self):self.live=False
 def wait(self,timeout=None):return 0
class Tests(unittest.TestCase):
 def test_transport_and_dialogue(self):
  folder=Path(tempfile.mkdtemp());files=[]
  for n in range(2):
   path=folder/(str(n)+".wav")
   with wave.open(str(path),"wb") as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(100);f.writeframes(b"\0\0"*1000)
   files.append(path)
  runtime=SimpleNamespace(settings={},lock=threading.RLock(),stop_event=threading.Event())
  c=dj.Controller(runtime);c.play_dialogue=[(1,"first"),(2,"second")];c.play_forced=True
  def until(condition):
   limit=time.monotonic()+3
   while not condition():
    if time.monotonic()>limit:self.fail("timed out: "+repr(c.playback_snapshot()))
    time.sleep(.01)
  with patch.object(dj.subprocess,"Popen",side_effect=Process):
   self.assertTrue(c.play(files,"ffplay"));until(lambda:c.playback_snapshot().get("text")=="first")
   self.assertTrue(c.playback_control("pause"));until(lambda:c.playback_snapshot().get("paused"))
   self.assertTrue(c.playback_control("seek",3));until(lambda:c.playback_snapshot().get("position",0)>=3)
   self.assertTrue(c.playback_control("next"));until(lambda:c.playback_snapshot().get("text")=="second")
   self.assertTrue(c.playback_snapshot()["paused"]);c.playback_control("resume");until(lambda:not c.playback_snapshot().get("paused",True))
   c.cancel_playback();c.play_thread.join(3);self.assertTrue(c.play_done)
 def test_reminder_cadence_and_resolution(self):
  import sys
  path=Path(__file__).resolve().parents[1]/"PAFPlayer.py"
  spec=importlib.util.spec_from_file_location("v677player",path);player=importlib.util.module_from_spec(spec);sys.modules[spec.name]=player;spec.loader.exec_module(player)
  schedule=player.HUDWarningSchedule()
  self.assertEqual(["warning"],schedule.start_track({"a":"warning"}))
  for _ in range(9):self.assertEqual([],schedule.start_track({"a":"warning"}))
  self.assertEqual(["warning"],schedule.start_track({"a":"warning"}))
  self.assertEqual([],schedule.start_track({}))
  self.assertEqual(["warning"],schedule.start_track({"a":"warning"}))
if __name__=="__main__":unittest.main()
