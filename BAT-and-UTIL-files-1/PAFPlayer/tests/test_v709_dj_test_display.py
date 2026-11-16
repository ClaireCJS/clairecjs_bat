import importlib.util,io,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("v709_player",Path(__file__).resolve().parents[1]/"PAFPlayer.py");player=importlib.util.module_from_spec(spec);sys.modules[spec.name]=player;spec.loader.exec_module(player)
import PAFPlayer_dj_test as dj
class Terminal(io.StringIO):
 def isatty(self):return True
class DisplayTests(unittest.TestCase):
 def test_colors_heading_error_and_cast(self):
  runtime=SimpleNamespace(settings={"ai_dj":{"interval":2,"seconds":75,"speakers":2,"women":1,"men":1,"accent":"British English"}})
  app=SimpleNamespace(load_playlist=lambda *a,**k:[Path("x.mp3")],paf_workflows=lambda:runtime,probe_audio_tags=lambda p:{"Artist":"Band","Song":"Song"},load_lyrics=lambda p:[]);out=Terminal()
  with patch.object(dj,"available_models",return_value=([("Ollama: model","ollama","model","")],[])),patch.object(dj,"generate",side_effect=RuntimeError("no")):
   self.assertEqual(1,dj.run(app,["a.m3u"],out))
  text=out.getvalue()
  for expected in (dj.CYAN+"Band",dj.YELLOW+"Song","\x1b#3","\x1b#4","\x1b#5",dj.ERROR+"⚠ Generation failed","75 seconds","British English","--ollamainstructions model","Actual instructions sent"):
   self.assertIn(expected,text)
 def test_redirected_headings_do_not_contain_terminal_line_modes(self):
  out=io.StringIO();dj.model_heading("Model",out);self.assertNotIn("\x1b#3",out.getvalue());self.assertIn("Model",out.getvalue())
 def test_stored_model_instructions_do_not_propose_download(self):
  out=io.StringIO()
  with patch.object(dj,"ollama_models",return_value=([],None)),patch.object(dj,"stored_ollama_models",return_value=["gpt-oss:120b"]):
   self.assertEqual(0,dj.ollama_instructions(["gpt-oss:120b"],out))
  self.assertIn("restart Ollama",out.getvalue());self.assertNotIn("ollama pull",out.getvalue())
 def test_invalid_model_name_is_rejected(self):
  out=io.StringIO();self.assertEqual(2,dj.ollama_instructions(["model & bad"],out));self.assertIn(dj.ERROR,out.getvalue())
if __name__=="__main__":unittest.main()
