"""Brief real-console A/B. Supervisor resumes the paused owner even on failure."""
import sys,json,ctypes,subprocess,time,os
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PID=323756
if '--worker' not in sys.argv:
 k=ctypes.WinDLL('kernel32',use_last_error=True);nt=ctypes.WinDLL('ntdll')
 k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_bool,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p
 nt.NtSuspendProcess.argtypes=[ctypes.c_void_p];nt.NtResumeProcess.argtypes=[ctypes.c_void_p]
 k.CloseHandle.argtypes=[ctypes.c_void_p]
 proc=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 handle=None;suspended=False
 try:
  while True:
   line=proc.stdout.readline()
   if line.strip()=='READY':break
   if not line:raise RuntimeError(proc.stderr.read())
  handle=k.OpenProcess(0x800,False,PID)
  if not handle:raise ctypes.WinError(ctypes.get_last_error())
  import urllib.request
  status=json.load(urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://127.0.0.1:666/api/status'))
  assert status['paused'],'Owner must remain paused before testing'
  assert nt.NtSuspendProcess(handle)==0;suspended=True
  out,err=proc.communicate('GO\n',timeout=35)
  print(out);print(err,file=sys.stderr)
  if proc.returncode:raise RuntimeError(f'worker exit {proc.returncode}')
 finally:
  if suspended:nt.NtResumeProcess(handle)
  if handle:k.CloseHandle(handle)
  if proc.poll() is None:proc.terminate()
else:
 import runpy,ast,statistics
 from unittest import mock
 d=runpy.run_path(str(ROOT/'tests/probe_v485_pipeline.py'))
 p=d['probe'].app;show=d['show'];ns=d['ns'];local=d['local']
 node=next(n for n in ast.parse((ROOT/'PAFPlayer.py.bak.202610011300.replaced-by-chatgpt.bak').read_text(encoding='utf-8-sig')).body if isinstance(n,ast.FunctionDef) and n.name=='render_drcs_visualizer')
 oldns=dict(vars(p));exec(compile(ast.Module(body=[node],type_ignores=[]),'<old>','exec'),oldns)
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.FreeConsole();assert k.AttachConsole(PID)
 report=sys.stdout
 print('READY',flush=True);assert sys.stdin.readline().strip()=='GO'
 stream=open('CONOUT$','w',encoding='utf-8')
 results=[]
 with mock.patch.object(p.sys,'stdout',stream),mock.patch.object(p.shutil,'get_terminal_size',return_value=os.terminal_size((170,47))):
  ns['write_console']=p.write_console
  p.write_console('\x1b[?1049h\x1b[2J\x1b[H\x1b[?25l')
  try:
   p.write_console(p.define_all_player_drcs(9))
   for version,target in [('old',120),('new',60),('new',90),('new',120),('old',120)]:
    ns['render_drcs_visualizer']=oldns['render_drcs_visualizer'] if version=='old' else p.render_drcs_visualizer
    local['reset_visualizer_transport_cache']()
    count=0;started=time.perf_counter();deadline=started;times=[]
    while time.perf_counter()-started<2.5:
     before=time.perf_counter();show(8+(before-started),'▶',visualizer_only=True);times.append((time.perf_counter()-before)*1000);count+=1
     deadline+=1/target
     remaining=deadline-time.perf_counter()
     if remaining>0:time.sleep(remaining)
     else:deadline=time.perf_counter()
    results.append(dict(version=version,target=target,fps=count/(time.perf_counter()-started),median_work_ms=statistics.median(times),p95_work_ms=sorted(times)[int(len(times)*.95)]))
  finally:
   p.write_console('\x1b(B\x1b[0m\x1b[?7h\x1b[?1049l')
 stream.close()
 print(json.dumps(results,indent=2),file=report,flush=True)
