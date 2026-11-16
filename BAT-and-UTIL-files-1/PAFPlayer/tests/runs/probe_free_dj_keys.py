"""Make minimal free-tier provider requests without printing keys or responses."""
import json,sys,urllib.error,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'src'))
import PAFPlayer_dj as d

def request(url,body,headers):
 req=urllib.request.Request(url,data=json.dumps(body).encode('utf8'),headers={'Content-Type':'application/json',**headers})
 try:
  with urllib.request.urlopen(req,timeout=90) as response:
   data=json.loads(response.read(2*1024*1024));print('HTTP',response.status,'response received:',bool(data),flush=True)
 except urllib.error.HTTPError as exc:
  try:
   error=json.loads(exc.read(65536)).get('error',{});status=error.get('status',error.get('code',''))
   if not isinstance(status,(str,int)) or len(str(status))>100:status=''
  except Exception:status=''
  print('HTTP',exc.code,'error code:',status,flush=True)
 except Exception as exc:print('Request failed:',type(exc).__name__,flush=True)

print('OpenRouter free-route test:',end=' ',flush=True)
request('https://openrouter.ai/api/v1/chat/completions',{'model':'openrouter/free','messages':[{'role':'user','content':'Say hello in one word.'}],'max_tokens':32},{'Authorization':'Bearer '+d.provider_key('OPENROUTER_API_KEY')})
print('Gemini free-tier test:',end=' ',flush=True)
request('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent',{'contents':[{'parts':[{'text':'Say hello in one word.'}]}],'generationConfig':{'maxOutputTokens':64}},{'x-goog-api-key':d.provider_key('GEMINI_API_KEY')})
