import importlib.util,json,threading,unittest
from pathlib import Path
from types import SimpleNamespace
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v670_dj_persist',root/'src/PAFPlayer_dj.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class Tests(unittest.TestCase):
 def test_named_prompt_and_previous_restore_survive_reload(self):
  saved=[];runtime=SimpleNamespace(settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda: saved.append(json.dumps(runtime.settings)))
  c=d.Controller(runtime);c.configure({'prompt_text':'Politics text','prompt_previous':'My old text','prompt_choice':'saved:Mine','prompt_presets':[{'name':'Mine','text':'Politics text'}]})
  other=SimpleNamespace(settings=json.loads(saved[-1]),lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None)
  c2=d.Controller(other)
  self.assertEqual('My old text',c2.options['prompt_previous']);self.assertEqual('saved:Mine',c2.options['prompt_choice']);self.assertEqual('Politics text',c2.options['prompt_presets'][0]['text'])
if __name__=='__main__':unittest.main()
