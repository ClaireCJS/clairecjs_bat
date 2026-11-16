import hashlib,os,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
folder=Path(tempfile.mkdtemp(prefix='v674-single-file-',dir=root/'tests/runs'))
source=root/'PAFPlayer.py';copy=folder/'PAFPlayer.py';shutil.copy2(source,copy)
assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256(copy.read_bytes()).digest()
code=r'''
import runpy,sys,tkinter
real=tkinter.Tk
def autoclose():
 window=real();window.after(700,window.destroy);return window
tkinter.Tk=autoclose
sys.argv=[sys.argv[1],'--models']
try:runpy.run_path(sys.argv[0],run_name='__main__')
except SystemExit as e:
 if e.code not in (0,None):raise
for name in ('PAFPlayer_dj','PAFPlayer_voice_models'):
 module=__import__(name)
 assert module.__file__.startswith(sys.argv[0]+'::'),(name,module.__file__)
print('Single copied player opened model window and loaded both features from its bundle.')
'''
result=subprocess.run([sys.executable,'-B','-I','-c',code,str(copy)],cwd=folder,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=45,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
print(result.stdout,end='')
if result.returncode:raise RuntimeError(result.stderr)
