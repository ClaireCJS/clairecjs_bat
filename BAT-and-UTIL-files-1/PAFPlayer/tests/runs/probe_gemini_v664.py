import json,sys,urllib.error,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'src'));import PAFPlayer_dj as dj
url='https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent'
body={'contents':[{'parts':[{'text':'Reply with hello.'}]}],'generationConfig':{'maxOutputTokens':100}}
request=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','x-goog-api-key':dj.provider_key('GEMINI_API_KEY')})
try:
 with urllib.request.urlopen(request,timeout=90) as response:
  data=json.load(response);parts=data.get('candidates',[{}])[0].get('content',{}).get('parts',[])
  print('Gemini native HTTP:',response.status,'text parts:',sum(bool(p.get('text')) for p in parts),flush=True)
except urllib.error.HTTPError as exc:
 try:data=json.loads(exc.read()).get('error',{});status=data.get('status','')
 except Exception:status=''
 print('Gemini native HTTP:',exc.code,'status:',status,flush=True)
except Exception as exc:print('Gemini failed:',type(exc).__name__,flush=True)
