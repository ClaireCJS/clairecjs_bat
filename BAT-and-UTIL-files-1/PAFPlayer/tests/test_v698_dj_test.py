import importlib.util, io, json, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("v698_player",Path(__file__).resolve().parents[1]/"PAFPlayer.py")
appmod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=appmod;spec.loader.exec_module(appmod)
import PAFPlayer_dj_test as comparison
from PAFPlayer_instance import Instance
class TestDJComparison(unittest.TestCase):
 def test_same_prompt_tracks_cast_and_color_for_all_models(self):
  rt=SimpleNamespace(settings={"ai_dj":{"interval":3,"history":10,"speakers":2}})
  app=SimpleNamespace(load_playlist=lambda *a,**k:[Path("one.mp3"),Path("two.mp3")],paf_workflows=lambda:rt,probe_audio_tags=lambda p:{"Artist":"band","Song":p.stem},load_lyrics=lambda p:[(0,1,"lyric")])
  out=io.StringIO();calls=[]
  def generate(dj,model,prompt,data,speakers):calls.append((prompt,data,speakers));return [(1,"A thoughtful comment.")]
  with patch.object(comparison,"available_models",return_value=([("one","x","",""),("two","x","","")],["missing model"])),patch.object(comparison,"generate",side_effect=generate):
   self.assertEqual(0,comparison.run(app,["playlist.m3u"],out))
  self.assertEqual(calls[0],calls[1]);self.assertEqual(3,len(json.loads(calls[0][1])["recent_tracks"]))
  for value in (comparison.YELLOW,comparison.RED,comparison.GREEN,"missing model"):self.assertIn(value,out.getvalue())
 def test_authenticated_playlist_snapshot_is_read_only(self):
  with tempfile.TemporaryDirectory() as tmp:
   rt=SimpleNamespace(root=Path(tmp),queue_read=lambda:{"entries":["a.mp3","b.mp3"],"next":[],"current":None,"playlist":"x","shuffled":False})
   inst=Instance(rt);inst.start()
   try:self.assertEqual(["a.mp3","b.mp3"],Instance(rt).forward({"dj_test_snapshot":True})["entries"])
   finally:inst.close()
 def test_random_visits_match_interval_and_include_next(self):
  class RNG:
   def choice(self,x):return x[0]
  self.assertEqual([Path("a")]*11,comparison.sample_tracks(["a"],10,RNG()))
if __name__=="__main__":unittest.main()
