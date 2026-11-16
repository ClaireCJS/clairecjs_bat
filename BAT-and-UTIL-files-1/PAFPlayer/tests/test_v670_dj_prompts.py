import ast, importlib.util, json, sys, threading, types, unittest
from pathlib import Path
from unittest import mock
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v670_dj',root/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)
source=(root/'PAFPlayer.py').read_text(encoding='utf8');tree=ast.parse(source)
nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('PAFHashCommandEntry','read_windows_key_action')]
nodes[-1].returns=None
for a in nodes[-1].args.args:a.annotation=None
clock=types.SimpleNamespace(now=0.,monotonic=lambda:clock.now)
ns={'os':types.SimpleNamespace(name='nt'),'time':clock};exec(compile(ast.Module(body=nodes,type_ignores=[]),'player','exec'),ns)
ns['_HASH_COMMAND_ENTRY']=ns['PAFHashCommandEntry']();ns['_HASH_COMMAND_PREFIX']='hash-command:'
class Tests(unittest.TestCase):
 def test_shift_holds_prompt_then_timer_restarts_on_release(self):
  held=[True];ns['_windows_key_down']=lambda key:held[0] and key==0x10
  m=types.SimpleNamespace(kbhit=lambda:False,getwch=lambda:'')
  e=ns['_HASH_COMMAND_ENTRY'];clock.now=0;e.feed('#',0);e.feed('d',0)
  with mock.patch.dict(sys.modules,{'msvcrt':m}):
   clock.now=8;self.assertIsNone(ns['read_windows_key_action']());self.assertEqual('d',e.buffer)
   clock.now=20;self.assertIsNone(ns['read_windows_key_action']());self.assertEqual('d',e.buffer)
   held[0]=False;clock.now=21.4;self.assertIsNone(ns['read_windows_key_action']());self.assertEqual('d',e.buffer)
   clock.now=21.5;self.assertEqual('hash-command:d',ns['read_windows_key_action']());self.assertIsNone(e.buffer)
 def test_prompt_defaults_presets_and_validation(self):
  o=dj.settings();self.assertIn('natural radio dialogue',o['prompt_text']);self.assertEqual('custom',o['prompt_choice']);self.assertEqual([],o['prompt_presets'])
  values={'prompt_text':'hello {speakers}', 'prompt_previous':'before','prompt_choice':'saved:Mine','prompt_presets':[{'name':'Mine','text':'first'}]}
  self.assertEqual(values['prompt_presets'],dj.settings(values)['prompt_presets'])
  with self.assertRaises(ValueError):dj.settings({'prompt_presets':[{'name':'a','text':'x'},{'name':'A','text':'y'}]})
 def test_provider_receives_selected_prompt_and_no_introductions(self):
  history=[{'artist':'Band','title':'Song'}];opts=dj.settings({'text_provider':'openrouter','prompt_text':'Custom {speakers} for {seconds} seconds'})
  calls=[]
  def post(url,data,headers=None,timeout=45):
   calls.append(data);return {'choices':[{'message':{'content':'[{"speaker":1,"text":"Hello"}]'}}]}
  with mock.patch.object(dj,'provider_key',return_value='test-key'),mock.patch.object(dj,'openai_key',return_value=''),mock.patch.object(dj,'post_json',side_effect=post):
   self.assertEqual([(1,'Hello')],dj.dialogue(history,opts)[0])
  messages=calls[0]['messages'];self.assertIn('Custom 2 for 90 seconds',messages[0]['content']);self.assertIn('Do not introduce the speakers',messages[0]['content']);self.assertEqual(history,json.loads(messages[1]['content'])['recent_tracks'])
 def test_random_includes_previous_builtin_and_saved_prompts(self):
  opts=dj.settings({'prompt_choice':'random','prompt_text':'current','prompt_previous':'previous','prompt_presets':[{'name':'Mine','text':'my custom'}], 'text_provider':'openrouter'})
  calls=[]
  def choose(items):calls.extend(items);return 'my custom'
  def post(url,data,headers=None,timeout=45):
   self.assertTrue(data['messages'][0]['content'].startswith('my custom'));return {'choices':[{'message':{'content':'[{"speaker":1,"text":"hi"}]'}}]}
  with mock.patch.object(dj.random,'choice',side_effect=choose),mock.patch.object(dj,'provider_key',return_value='test-key'),mock.patch.object(dj,'openai_key',return_value=''),mock.patch.object(dj,'post_json',side_effect=post):dj.dialogue([{'artist':'a','title':'b'}],opts)
  for t in ('current','previous','my custom',dj.ORIGINAL_DJ_PROMPT,dj.POLITICS_DJ_PROMPT):self.assertIn(t,calls)
if __name__=='__main__':unittest.main()
