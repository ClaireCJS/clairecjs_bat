"""Isolated UI fixture: no audio playback, native UI, or real user settings writes."""
from pathlib import Path
import time
import uuid
from unittest import mock
import PAFPlayer as p
from PAFPlayer_workflows import Runtime,write_json
from PAFPlayer_web_workflows import calculate_queue_edit,queue_snapshot
from test_PAFPlayer_workflows import fixture

root=Path(__file__).parent/('paf456-preview-'+uuid.uuid4().hex[:8]);root.mkdir()
runtime=Runtime(p,root/'settings');runtime.settings['remote_uploads']=False
runtime.settings['library_roots']=[str(root)]
paths=[str(fixture(root,name+'.wav')) for name in ('Preview One','Preview Two','Preview Three')]
missing=str(root/'Missing Song.wav')
state={'entries':paths+[missing],'next':[],'current':paths[0],'playlist':str(root/'preview.m3u8'),'reason':'Preview history-biased shuffle: oldest known play first','shuffled':True,'missing':[missing]}
(root/'preview.m3u8').write_text('\n'.join(paths+[missing])+'\n',encoding='utf-8')
runtime.queue_read=lambda:state
def edit(payload):
    global state
    result=calculate_queue_edit(runtime,state,payload)
    if payload.get('op')!='save':state=result
    return result if payload.get('op')=='save' else queue_snapshot(runtime)
runtime.queue_bridge=edit
server=p.PAFWebServer(host='127.0.0.1',port=18056);server.workflows=runtime;runtime.server=server
server._current_audio=Path(paths[0]);server._playlist_snapshot_callback=lambda **kw:{'active':True,'items':[{'path':x,'filename':Path(x).name,'index':i+1,'current':i==0,'queued':False} for i,x in enumerate(paths)],'total':len(paths),'offset':0,'limit':100,'queue':[]}
server.timeline_snapshot=lambda:{'source':'track','position':4,'ui_start':0,'speed':1,'playing':False,'clock_epoch':time.time(),'start_frame':0,'fps':30,'width':64,'frames':''}
server.publish(playing=True,paused=True,duration_seconds=120,position_seconds=4,lyric='Ten of my fingers',lyrics=[[0,None,'Ten of my fingers']],track={'filename':'Preview One.wav','title':'Preview One','artist':'Synthetic fixture'})
prefs={}
with mock.patch.object(p,'load_web_ui_preferences',side_effect=lambda:dict(prefs)),mock.patch.object(p,'save_web_ui_preferences',side_effect=lambda value:(prefs.update(value) or dict(prefs))):
    assert server.start();print(server.url,flush=True)
    (root/'preview-server.txt').write_text(server.url,encoding='utf-8')
    try:
        while True:time.sleep(.5)
    except KeyboardInterrupt:pass
    finally:server.close();runtime.close()
