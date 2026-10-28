"""Preserved native and real-player settings integration checks; no live settings writes."""
from pathlib import Path
from datetime import datetime
import sys, subprocess, json, hashlib, re
testing=Path(__file__).resolve().parent
side=testing.parent
sys.path.insert(0,str(side/'tools'))
from build_PAFPlayer_screensaver import build
out=testing/'old'/('settings-multimonitor-'+datetime.now().strftime('%Y%m%d-%H%M%S'));out.mkdir()
exe=build(side,out/'PAFPlayer.scr')
csc='C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'
def compile_exe(main,sources,dest):
 subprocess.run([csc,'/nologo','/target:exe','/platform:x64','/main:'+main,'/out:'+str(dest),'/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.Web.Extensions.dll',str(side/'src'/'PAFPlayer_screensaver.cs'),*[str(x) for x in sources]],check=True)
compile_exe('SaverTests',[testing/'test_PAFPlayer_screensaver.cs'],out/'tests.exe')
r=subprocess.run([str(out/'tests.exe'),str(out),str(exe)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
with (out/'native-results.txt').open('x',encoding='utf-8') as f:f.write(r.stdout+'\n'+r.stderr)
print(r.stdout[-1800:],r.stderr,flush=True)
if r.returncode:sys.exit(r.returncode)
compile_exe('SettingsIntegration',[testing/'settings_api_integration.cs'],out/'settings-integration.exe')
sys.path.insert(0,str(side.parent));sys.argv=['PAFPlayer.py','--unit-tests']
import PAFPlayer as app
from PAFPlayer_workflows import Runtime
from unittest import mock
runtime=Runtime(app,out/'isolated-settings')
with mock.patch.object(app,'paf_workflows',return_value=runtime):server=app.PAFWebServer(host='127.0.0.1',port=0)
try:
 with mock.patch.object(app,'append_pafplayer_trace'):assert server.start()
 integration=subprocess.run([str(out/'settings-integration.exe'),str(server.port)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=15,creationflags=subprocess.CREATE_NO_WINDOW)
 print(integration.stdout,integration.stderr,flush=True)
 assert integration.returncode==0
 assert runtime.settings['visual_screensaver']['enabled'] is True
 assert runtime.settings['visual_screensaver']['brightness']==37
 assert json.loads((runtime.root/'settings.json').read_text())['visual_screensaver']['brightness']==37
finally:server.close()
manifest={'checks':int(re.search(r'COMPLETE: (\d+) checks passed',r.stdout).group(1)),'real_player_settings_integration':'passed','sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((side/'src'/'PAFPlayer_screensaver.cs').read_bytes()).hexdigest(),'source':str(exe)}
with (out/'verified.json').open('x',encoding='utf-8') as f:json.dump(manifest,f,indent=2)
print('VERIFIED',out)
