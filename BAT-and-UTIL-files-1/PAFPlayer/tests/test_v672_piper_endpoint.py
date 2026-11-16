import importlib.util,io,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
spec=importlib.util.spec_from_file_location('v672_web',root/'src/PAFPlayer_web_workflows.py');web=importlib.util.module_from_spec(spec);spec.loader.exec_module(web)
class Handler:
 def __init__(self,payload):
  self.command='POST';raw=json.dumps(payload).encode();self.headers={'Content-Length':str(len(raw))};self.rfile=io.BytesIO(raw);self.connection=SimpleNamespace(settimeout=lambda _:None);self.response=None
 def _json(self,code,data):self.response=(code,data)
class Tests(unittest.TestCase):
 def test_authorized_retry_starts_setup(self):
  h=Handler({'setup_piper':True});owner=SimpleNamespace(workflows=object());controller=SimpleNamespace(start_piper_setup=mock.Mock(return_value=True))
  with mock.patch.object(web,'authorized',return_value=True),mock.patch.dict(sys.modules,{'PAFPlayer_dj':SimpleNamespace(get_controller=lambda _:controller)}):
   self.assertTrue(web.handle(h,owner,'/api/workflows/dj'))
  controller.start_piper_setup.assert_called_once_with(force=True);self.assertEqual((200,{'started':True}),h.response)
 def test_remote_retry_is_rejected(self):
  h=Handler({'setup_piper':True});owner=SimpleNamespace(workflows=object());controller=SimpleNamespace(start_piper_setup=mock.Mock())
  with mock.patch.object(web,'authorized',return_value=False),mock.patch.dict(sys.modules,{'PAFPlayer_dj':SimpleNamespace(get_controller=lambda _:controller)}):
   self.assertTrue(web.handle(h,owner,'/api/workflows/dj'))
  controller.start_piper_setup.assert_not_called();self.assertEqual(403,h.response[0])
if __name__=='__main__':unittest.main()
