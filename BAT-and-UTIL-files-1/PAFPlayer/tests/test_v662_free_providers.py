import importlib.util,io,json,os,tempfile,threading,unittest,urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v662_dj_candidate',ROOT/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)
HISTORY=[{'artist':'Example Artist','title':'Example Song'}]
PAYLOAD='[{"speaker":1,"text":"Hello"}]'

class Tests(unittest.TestCase):
 def test_auto_falls_through_to_only_free_openrouter_model(self):
  calls=[]
  def post(url,data,headers=None,timeout=None):
   calls.append((url,data))
   if 'api.openai.com' in url:raise urllib.error.HTTPError(url,429,'',{},io.BytesIO(b'{"error":{"code":"credit_balance_exhausted"}}'))
   return {'choices':[{'message':{'content':PAYLOAD}}]}
  with mock.patch.object(dj,'openai_key',return_value='fake-openai'),mock.patch.object(dj,'provider_key',side_effect=lambda k:'fake-router' if k=='OPENROUTER_API_KEY' else ''),mock.patch.object(dj,'post_json',side_effect=post):
   rows,warning=dj.dialogue(HISTORY,dj.settings())
  self.assertEqual([(1,'Hello')],rows);self.assertIn('openrouter',warning)
  self.assertEqual('openrouter/free',calls[-1][1]['model']);self.assertEqual(2,len(calls))
 def test_gemini_requires_explicit_free_tier_confirmation(self):
  opts=dj.settings({'text_provider':'gemini'})
  with mock.patch.object(dj,'provider_key',return_value='fake-gemini'),mock.patch.object(dj,'post_json') as post,mock.patch.object(dj.urllib.request,'urlopen',side_effect=OSError('offline')):
   with self.assertRaises(OSError):dj.dialogue(HISTORY,opts)
   post.assert_not_called()
  opts=dj.settings({'text_provider':'gemini','gemini_free_confirmed':True})
  with mock.patch.object(dj,'provider_key',return_value='fake-gemini'),mock.patch.object(dj,'post_json',return_value={'candidates':[{'content':{'parts':[{'text':PAYLOAD}]}}]}) as post:
   rows,_=dj.dialogue(HISTORY,opts)
  self.assertEqual([(1,'Hello')],rows);self.assertIn('generativelanguage.googleapis.com',post.call_args.args[0])
  self.assertIn('gemini-3.5-flash-lite:generateContent',post.call_args.args[0]);self.assertEqual('fake-gemini',post.call_args.args[2]['x-goog-api-key'])
 def test_credit_warning_persists_and_clears_only_for_same_key(self):
  root=Path(tempfile.mkdtemp(prefix='dj-credit-test-'));r=SimpleNamespace(root=root)
  with mock.patch.object(dj,'openai_key',return_value='sk-'+('a'*40)):
   warning=dj.CreditWarnings(r);warning.set(True);self.assertTrue(dj.CreditWarnings(r).messages())
   warning.set(False);self.assertFalse(dj.CreditWarnings(r).messages())
   warning.set(True)
  with mock.patch.object(dj,'openai_key',return_value='sk-'+('b'*40)):self.assertFalse(dj.CreditWarnings(r).messages())
  self.assertNotIn('sk-',str([p.read_text() for p in (root/'dj-credit-warnings').glob('*.json')]))
 def test_rate_limit_is_not_automatically_credit_exhaustion(self):
  e=urllib.error.HTTPError('https://example.test',429,'',{},io.BytesIO(b'{"error":{"code":"rate_limit_exceeded"}}'))
  self.assertEqual('',dj.openai_error_code(e))

if __name__=='__main__':unittest.main()
