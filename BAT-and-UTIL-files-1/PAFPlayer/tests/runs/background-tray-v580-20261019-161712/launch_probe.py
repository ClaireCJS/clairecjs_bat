ROOT='C:\\codex\\clairevironment\\bat\\PAFPlayer'
CHILD_REPORT='C:\\codex\\clairevironment\\bat\\PAFPlayer\\tests\\reports\\background-tray-v580-20261019-161712-child.json'

import os, sys, json, threading, time
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
    result=original(controller); events.append({'native_started':result,'at':time.time()})
    timer=threading.Timer(5,lambda:controller.dispatch('exit'));timer.daemon=True;timer.start()
    return result
tray.TrayController.start=start
began=time.monotonic()
code=app.main(args)
if '--foreground' in args:
    with Path(CHILD_REPORT).open('x',encoding='utf-8') as output:
        json.dump({'exit_code':code,'seconds':time.monotonic()-began,'events':events},output)
raise SystemExit(code)
