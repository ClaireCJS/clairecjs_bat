"""Probe the DJ's configured OpenAI models without exposing credentials."""
from pathlib import Path
import json, os, sys, tempfile, urllib.error, urllib.request, wave

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'src'))
import PAFPlayer_dj as dj

key=os.environ.get('OPENAI_API_KEY','')
headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
request=urllib.request.Request('https://api.openai.com/v1/responses',
    data=json.dumps({'model':'gpt-6-luna','input':'Reply with the word ready.'}).encode('utf8'),headers=headers)
try:
    with urllib.request.urlopen(request,timeout=60) as response:
        body=json.loads(response.read())
        print('Text HTTP:',response.status,'response status:',body.get('status'),flush=True)
except urllib.error.HTTPError as exc:
    try:error=json.loads(exc.read()).get('error',{})
    except Exception:error={}
    print('Text HTTP:',exc.code,'error type:',error.get('type'),'error code:',error.get('code'),flush=True)
except Exception as exc:
    print('Text request failed:',type(exc).__name__,flush=True)

folder=Path(tempfile.mkdtemp(prefix='v660-openai-speech-',dir=str(root/'tests/runs')))
target=folder/'test.wav'
try:
    dj.speech_openai('The DJ is ready.','marin','neutral','gpt-realtime-2.1-mini',target)
    with wave.open(str(target),'rb') as wav:
        print('Speech WAV frames:',wav.getnframes(),'rate:',wav.getframerate(),flush=True)
except Exception as exc:
    print('Speech request failed:',type(exc).__name__,'HTTP status:',getattr(exc,'status_code',None),flush=True)
