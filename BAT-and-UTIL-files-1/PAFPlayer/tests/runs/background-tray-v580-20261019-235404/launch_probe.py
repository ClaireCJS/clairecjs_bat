ROOT='C:\\codex\\clairevironment\\bat\\PAFPlayer'
CHILD_REPORT='C:\\codex\\clairevironment\\bat\\PAFPlayer\\tests\\reports\\background-tray-v580-20261019-235404-child.json'

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
