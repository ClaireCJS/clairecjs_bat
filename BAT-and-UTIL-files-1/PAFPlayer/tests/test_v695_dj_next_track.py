import importlib.util,json,threading,unittest
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parents[1]/"src/PAFPlayer_dj.py"
s=importlib.util.spec_from_file_location("dj_v695",p);d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
class Tests(unittest.TestCase):
 def test_stale_prediction_is_discarded(self):
  c=d.Controller.__new__(d.Controller);c.lock=threading.RLock();c._upcoming_path=r"C:\music\b.mp3";c.forced=False;c.serial=2;c.ready=["audio"];c.ready_dialogue=[];c.ready_artwork=None;c.working=None;c.attempted=3;c.stage="Ready";c.log=type("Log",(),{"write":lambda *a,**k:None})()
  self.assertTrue(c.validate_upcoming(r"C:\music\b.mp3"));self.assertTrue(c.ready)
  self.assertFalse(c.validate_upcoming(r"C:\music\other.mp3"));self.assertIsNone(c.ready);self.assertEqual(3,c.serial)
 def test_prompt_receives_upcoming_and_requests_criticism(self):
  opts=d.settings({"text_provider":"auto"});opts["_upcoming_track"]={"artist":"A","title":"B"};calls=[]
  def post(url,data,headers=None,timeout=None):
   calls.append(data);return {"output":[{"content":[{"type":"output_text","text":"[{\"speaker\":1,\"text\":\"Hello\"}]"}]}]}
  with patch.object(d,"openai_key",return_value="fake"),patch.object(d,"post_json",side_effect=post):d.dialogue([{"artist":"C","title":"D","lyrics":"reference lyric"}],opts)
  self.assertEqual("B",json.loads(calls[0]["input"])["upcoming_track"]["title"]);self.assertIn("never quote or list lyric lines",calls[0]["instructions"])
 def test_unknown_upcoming_is_not_invented(self):
  opts=d.settings({"text_provider":"auto"});calls=[]
  def post(url,data,headers=None,timeout=None):
   calls.append(data);return {"output":[{"content":[{"type":"output_text","text":"[{\"speaker\":1,\"text\":\"Hello\"}]"}]}]}
  with patch.object(d,"openai_key",return_value="fake"),patch.object(d,"post_json",side_effect=post):d.dialogue([{"artist":"C","title":"D"}],opts)
  self.assertNotIn("upcoming_track",json.loads(calls[0]["input"]));self.assertIn("No actual next track is provided",calls[0]["instructions"])
if __name__=="__main__":unittest.main()
