import importlib.util,sys,json,unittest
from pathlib import Path
from unittest import mock
spec=importlib.util.spec_from_file_location('v679',str(Path(__file__).resolve().parents[1]/'PAFPlayer.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
import PAFPlayer_dj as d
import PAFPlayer_voice_models as v
class Tests(unittest.TestCase):
 def test_models_get_same_inputs_and_explicit_free_endpoints(self):
  calls=[]
  def chat(url,key,model,prompt,data,speakers):calls.append((model,prompt,data));return [(1,model)]
  with mock.patch.object(d,'provider_key',return_value='fake'),mock.patch.object(d,'_chat_dialogue',side_effect=chat):
   rows=v.compare_text(['gpt-oss-hosted','openrouter-free'],'same prompt',json.dumps(v.TEXT_EXAMPLE))
  self.assertEqual(['ok','ok'],[x['status'] for x in rows]);self.assertEqual('openai/gpt-oss-120b:free',calls[0][0]);self.assertEqual('openrouter/free',calls[1][0]);self.assertEqual(calls[0][1:],calls[1][1:])
 def test_failure_is_reported_then_other_model_runs(self):
  with mock.patch.object(d,'provider_key',return_value='fake'),mock.patch.object(d,'_chat_dialogue',side_effect=[ValueError('unavailable'),[(1,'okay')]]):
   rows=v.compare_text(['gpt-oss-hosted','openrouter-free'],'prompt','{}')
  self.assertEqual(['error','ok'],[x['status'] for x in rows]);self.assertIn('unavailable',rows[0]['error'])
 def test_local_install_is_explicit(self):
  with mock.patch.object(v,'local_ollama_executable',return_value='ollama.exe'),mock.patch.object(v,'run_command') as run:v.install_text_model()
  self.assertEqual(['ollama.exe','pull','gpt-oss:120b'],run.call_args.args[0])
 def test_gptoss_precedes_router_and_falls_back(self):
  calls=[]
  def chat(url,key,model,prompt,data,speakers):
   calls.append(model)
   if model.endswith('120b:free'):raise ValueError('not found')
   return [(1,'fresh dialogue')]
  with mock.patch.object(d,'provider_key',return_value='fake'),mock.patch.object(d,'_chat_dialogue',side_effect=chat),mock.patch.object(d,'openai_key',return_value=''):
   result,_=d.dialogue([{'artist':'a','title':'b'}],d.settings({'text_provider':'openrouter'}))
  self.assertEqual(['openai/gpt-oss-120b:free','openrouter/free'],calls);self.assertEqual('fresh dialogue',result[0][1])
if __name__=='__main__':unittest.main()
