import importlib.util,subprocess,time,json,sys
from pathlib import Path
root=Path.cwd();spec=importlib.util.spec_from_file_location('startup_cache',root/'src/PAFPlayer_startup_cache.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
results=[]
for mode in ('source','cached','cached'):
 start=time.perf_counter()
 command=[sys.executable,'-B',str(root/'PAFPlayer.py'),'--paf-audio-worker'] if mode=='source' else c.audio_worker_command(root/'PAFPlayer.py')
 p=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 results.append({'mode':mode,'seconds':round(time.perf_counter()-start,3),'exit_code':p.returncode,'used_source_fallback':b'runpy' in p.stderr})
print(json.dumps(results))
path=Path('tests/reports/v761-native-worker-startup-benchmark.json');assert not path.exists();path.write_text(json.dumps(results,indent=2),encoding='utf-8')
