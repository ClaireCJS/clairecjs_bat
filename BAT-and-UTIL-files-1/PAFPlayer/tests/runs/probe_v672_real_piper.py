import importlib.util,os,subprocess,tempfile,wave
from pathlib import Path
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v672_real_piper',root/'src/PAFPlayer_dj.py');dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)
installed=dj.installed_piper()
if not installed:raise SystemExit('No completed Piper installation found')
folder=Path(tempfile.mkdtemp(prefix='v672-piper-',dir=root/'tests/runs'));output=folder/'test.wav'
result=subprocess.run([installed[0],'-m',installed[1],'-f',str(output),'--','Piper local speech is ready.'],capture_output=True,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
if result.returncode:raise SystemExit('Piper returned a nonzero exit status')
with wave.open(str(output),'rb') as wav:
 if wav.getnframes()<=0:raise SystemExit('Piper created empty audio')
 print('Real local Piper synthesis passed:',wav.getnframes(),'frames at',wav.getframerate(),'Hz')
