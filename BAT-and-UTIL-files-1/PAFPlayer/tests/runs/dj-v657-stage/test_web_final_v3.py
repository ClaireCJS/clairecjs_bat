import importlib.util,io,json,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
path=Path(__file__).parent/'PAFPlayer_candidate_v10.py';spec=importlib.util.spec_from_file_location('paf_dj_api',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
import PAFPlayer_web_workflows as api
class Runtime:
 def __init__(self):self.settings={};self.lock=threading.RLock();self.stop_event=threading.Event();self.token='example-token';self.saved=0
 def save_settings(self):self.saved+=1
 def log(self,*a,**k):pass
class Handler:
 def __init__(self,payload=None,token='example-token',local=True):
  self.command='POST' if payload is not None else 'GET';self.path='/api/workflows/dj';self.local=local
  data=json.dumps(payload or {}).encode();self.rfile=io.BytesIO(data);self.headers={'Host':'127.0.0.1:8811','Content-Length':str(len(data)),'X-PAF-Workflow-Token':token};self.connection=SimpleNamespace(settimeout=lambda n:None)
 def _client_is_local(self):return self.local
 def _json(self,code,data):self.code=code;self.data=data
class ApiTests(unittest.TestCase):
 def test_persist_balancing_and_reload(self):
  r=Runtime();owner=SimpleNamespace(host='127.0.0.1',port=8811,workflows=r);h=Handler({'enabled':True,'speakers':10,'men':3})
  self.assertTrue(api.handle(h,owner,h.path));self.assertEqual(200,h.code);self.assertEqual(7,r.settings['ai_dj']['women']);self.assertEqual(1,r.saved)
  h=Handler();api.handle(h,owner,h.path);self.assertEqual(3,h.data['settings']['men']);self.assertNotIn('OPENAI_API_KEY',str(h.data))
 def test_rejects_bad_token_and_cross_origin(self):
  r=Runtime();owner=SimpleNamespace(host='127.0.0.1',port=8811,workflows=r);h=Handler({'enabled':True},token='wrong');api.handle(h,owner,h.path);self.assertEqual(403,h.code);self.assertEqual({},r.settings)
  h=Handler({'enabled':True});h.headers['Origin']='https://attacker.example';api.handle(h,owner,h.path);self.assertEqual(403,h.code)
if __name__=='__main__':unittest.main()
