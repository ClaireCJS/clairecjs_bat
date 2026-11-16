import importlib.util,json,sys,unittest,urllib.request,urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("v713_player",Path(__file__).resolve().parents[1]/"PAFPlayer.py");player=importlib.util.module_from_spec(spec);sys.modules[spec.name]=player;spec.loader.exec_module(player)
import PAFPlayer_remote_mouse as remote
class Backend:
 def __init__(self):self.events=[]
 def move(self,x,y):self.events.append(("move",x,y))
 def click(self,button):self.events.append(("click",button))
class Tests(unittest.TestCase):
 def test_disabled_and_rate_limited(self):
  self.assertFalse(remote.RemoteMouse(False).enabled)
  m=remote.RemoteMouse(True,Backend());wrong="0"*8 if m.code!="0"*8 else "1"*8
  for i in range(5):self.assertFalse(m.authorize("one",wrong)[0])
  self.assertFalse(m.authorize("one",m.code)[0]);self.assertTrue(m.authorize("two",m.code)[0])
 def test_player_http_routes_and_security(self):
  backend=Backend()
  with patch.object(player,"paf_workflows",return_value=SimpleNamespace()):
   server=player.PAFWebServer(enabled=True,host="127.0.0.1",port=0);server.remote_mouse=remote.RemoteMouse(True,backend);self.assertTrue(server.start())
   try:
    base="http://127.0.0.1:"+str(server.port);opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def post(path,body,code,origin=None):
     req=urllib.request.Request(base+path,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","X-PAF-Mouse-Code":code,"Origin":origin or base})
     try:
      with opener.open(req,timeout=3) as result:return result.status
     except urllib.error.HTTPError as exc:return exc.code
    with opener.open(base+"/remote-mouse",timeout=3) as response:self.assertIn(b"Left click",response.read())
    self.assertIn('href="/remote-mouse"',player._paf_web_html())
    code=server.remote_mouse.code;wrong="0"*8 if code!="0"*8 else "1"*8
    self.assertEqual(403,post("/api/paf-mouse/pair",{},wrong));self.assertEqual(403,post("/api/paf-mouse/pair",{},code,"http://evil.example"))
    self.assertEqual(200,post("/api/paf-mouse/pair",{},code));self.assertEqual(200,post("/api/paf-mouse/control",{"action":"move","dx":8,"dy":-6},code));self.assertEqual(200,post("/api/paf-mouse/control",{"action":"click","button":"right"},code));self.assertEqual(400,post("/api/paf-mouse/control",{"action":"move","dx":1000,"dy":0},code));self.assertEqual([("move",8,-6),("click","right")],backend.events)
    server.remote_mouse.enabled=False;self.assertEqual(403,post("/api/paf-mouse/control",{"action":"click","button":"left"},code))
   finally:server.close()
if __name__=="__main__":unittest.main()
