from pathlib import Path
import json,time,sys,subprocess,tempfile
import PAFPlayer as app
from PAFPlayer_startup_cache import AnalysisCache,audio_worker_command
root=Path.cwd();fixture=Path(tempfile.mkdtemp(prefix='v761-benchmark-',dir=root/'tests/runs'));cache=AnalysisCache(fixture/'analysis')
app.track_analysis_cache=lambda:cache
track=None
for line in reversed(Path(r'C:\logs\PAFPlayer\trace.log').read_text(encoding='utf-8',errors='replace').splitlines()):
 if ' track.prepare {' in line:
  record=json.loads('{'+line.partition(' {')[2]);candidate=Path(record['path'])
  if candidate.is_file():track=candidate;break
assert track
analysis=[]
for mode in ('cold-analysis','cached-analysis'):
 app._AUDIO_METADATA_CACHE.clear();app._EDGE_SILENCE_BOUNDS_CACHE.clear();start=time.perf_counter()
 duration,tags=app.probe_audio_metadata(track);bounds=app.detect_edge_silence_bounds(track,duration,enabled=True)
 analysis.append({'mode':mode,'seconds':round(time.perf_counter()-start,3),'duration':duration,'bounds':bounds})
worker=[]
for mode in ('source','first-cache-request','warm-cache'):
 if mode=='warm-cache':
  cmd=audio_worker_command(root/'PAFPlayer.py');deadline=time.monotonic()+30
  while '-c' not in cmd and time.monotonic()<deadline:time.sleep(.1);cmd=audio_worker_command(root/'PAFPlayer.py')
 start=time.perf_counter()
 cmd=[sys.executable,'-B',str(root/'PAFPlayer.py'),'--paf-audio-worker'] if mode=='source' else audio_worker_command(root/'PAFPlayer.py')
 result=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 worker.append({'mode':mode,'seconds':round(time.perf_counter()-start,3),'exit_code':result.returncode,'uses_compiled_code':'-c' in cmd})
report={'analysis':analysis,'worker_load_only':worker,'note':'Same installed Python, no audio output. Expected worker exit 1 on empty config. These are component measurements, not end-to-end playback latency.'}
path=root/'tests/reports/v761-final-startup-benchmark.json';assert not path.exists();path.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
