"""Real detached parent/child launch, native tray start and Exit; isolated settings."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run_PAFPlayer_tests import unique

stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
stage = unique(ROOT/'tests/runs'/('background-tray-v580-'+stamp)); stage.mkdir()
reports = ROOT/'tests/reports'
report = unique(reports/('background-tray-v580-'+stamp+'.json'))
child_report = unique(reports/('background-tray-v580-'+stamp+'-child.json'))
data = (ROOT/'PAFPlayer.py').read_bytes()
with (stage/'PAFPlayer.py').open('xb') as output: output.write(data)
wrapper = stage/'launch_probe.py'
source = r'''
import os, sys, json, threading, time, ctypes
from pathlib import Path
stage = Path(__file__).resolve().parent
work = stage/'settings'; work.mkdir(exist_ok=True)
for key in ('APPDATA','LOCALAPPDATA','TEMP','TMP'): os.environ[key]=str(work)
sys.path.insert(0, ROOT)
from run_PAFPlayer_tests import install_guards
install_guards(Path(ROOT)/'tests')
sys.path.insert(0,str(stage))
args=sys.argv[1:]; sys.argv=[str(stage/'PAFPlayer.py'),'--unit-tests']
import PAFPlayer as app
import PAFPlayer_remote_tray as remote
import PAFPlayer_tray as tray
remote.RemoteServer.start_polling=lambda self: None
remote.RemoteServer.close=lambda self: None
app.__file__=str(Path(__file__).resolve())  # The child uses this same isolated bootstrap.
events=[]
original=tray.TrayController.start
def start(controller):
    result=original(controller)
    kernel=ctypes.WinDLL('kernel32');kernel.GetConsoleWindow.restype=ctypes.c_void_p
    events.append({'native_started':result,'at':time.time(),'console_window':int(kernel.GetConsoleWindow() or 0)})
    marker=stage/'reload-started.json'
    action='exit' if marker.exists() else 'reload'
    events[-1]['action']=action
    if action=='reload':
        with marker.open('x',encoding='utf-8') as output:json.dump(events,output)
    timer=threading.Timer(5 if action=='exit' else 1,lambda:controller.dispatch(action));timer.daemon=True;timer.start()
    return result
tray.TrayController.start=start
began=time.monotonic()
code=app.main(args)
if '--foreground' in args and events and events[-1]['action']=='exit':
    with Path(CHILD_REPORT).open('x',encoding='utf-8') as output:
        json.dump({'exit_code':code,'seconds':time.monotonic()-began,'events':events},output)
raise SystemExit(code)
'''
source = 'ROOT='+repr(str(ROOT))+'\nCHILD_REPORT='+repr(str(child_report))+'\n'+source
with wrapper.open('x', encoding='utf-8') as output: output.write(source)
started = time.monotonic()
parent = subprocess.run([sys.executable,'-B','-X','utf8',str(wrapper),'--tray-only','127.0.0.1:39579'],
                        capture_output=True, text=True, encoding='utf-8', timeout=20)
parent_seconds = time.monotonic()-started
deadline = time.monotonic()+20
while not child_report.exists() and time.monotonic()<deadline:
    time.sleep(.2)
child = json.loads(child_report.read_text(encoding='utf-8')) if child_report.exists() else None
logs = list((stage/'settings/PAFPlayer/RemoteTray/logs').glob('*.log'))
result = {'stage':str(stage),'source_sha256':hashlib.sha256(data).hexdigest(),
          'parent_seconds':parent_seconds,'parent_exit':parent.returncode,
          'parent_stdout':parent.stdout,'parent_stderr':parent.stderr,'child':child,
          'child_report':str(child_report),'logs':[str(path) for path in logs], 'before_reload':json.loads((stage/'reload-started.json').read_text()) if (stage/'reload-started.json').exists() else []}
result['successful'] = bool(parent.returncode==0 and parent_seconds<5 and child and
    child['exit_code']==0 and child['seconds']>=5 and child['events'][0]['native_started'] and
    child['events'][0]['console_window']==0 and len(logs)==2 and all('Traceback' not in path.read_text(encoding='utf-8',errors='replace') for path in logs))
with report.open('x',encoding='utf-8') as output: json.dump(result,output,indent=2)
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['successful'] else 1)
