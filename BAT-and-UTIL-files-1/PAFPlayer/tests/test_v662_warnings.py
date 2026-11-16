import importlib.util,io,json,sys,tempfile,threading,time,unittest,urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v662_warn_source',ROOT/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)
spec=importlib.util.spec_from_file_location('v662_warn_player',ROOT/'PAFPlayer.py')
p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)

class Tests(unittest.TestCase):
 def test_real_job_event_persists_quota_warning_for_help_and_api(self):
  runtime=SimpleNamespace(root=Path(tempfile.mkdtemp(prefix='v662-warning-')),settings={},lock=threading.RLock(),stop_event=threading.Event(),save_settings=lambda:None)
  def post(url,data,headers=None,timeout=None):
   if 'api.openai.com' in url:raise urllib.error.HTTPError(url,429,'',{},io.BytesIO(b'{"error":{"code":"credit_balance_exhausted"}}'))
   return {'choices':[{'message':{'content':'[{"speaker":1,"text":"hello"}]'}}]}
  key='sk-'+('x'*32)
  with mock.patch.object(dj,'openai_key',return_value=key),mock.patch.object(dj,'provider_key',side_effect=lambda n:'router-key' if n=='OPENROUTER_API_KEY' else ''),mock.patch.object(dj,'post_json',side_effect=post),mock.patch.object(dj,'speech_openai',side_effect=RuntimeError('offline')),mock.patch.object(dj,'ensure_piper',side_effect=dj.PiperSetupError('unavailable')):
   c=dj.Controller(runtime);c.start(True,current={'artist':'private-artist','title':'private-title'})
   deadline=time.monotonic()+2
   while c.working is not None and time.monotonic()<deadline:time.sleep(.005)
   self.assertIn('credit balance was exhausted',' '.join(c.status()['warnings']))
   self.assertIn('WARNING:', ' '.join(p.dj_help_rows(c,80)))
   self.assertTrue(dj.CreditWarnings(runtime).messages())
   observed=''.join(f.read_text() for f in (runtime.root/'dj-credit-warnings').glob('*'))
   self.assertNotIn(key,observed);self.assertNotIn('private-artist',observed)
 def test_warning_tab_is_last_and_updates_from_status(self):
  html=p._paf_web_html()
  self.assertIn("['warningsSection','Warnings']",html)
  self.assertIn("frame.appendChild(section)",html)
  self.assertIn("getElementById('djWarningsContent')",html)
  self.assertIn('gemini_free_confirmed',html)
  self.assertLess(html.index("['workflowLogsSection','Logs']"),html.index("['warningsSection','Warnings']"))

if __name__=='__main__':unittest.main()
