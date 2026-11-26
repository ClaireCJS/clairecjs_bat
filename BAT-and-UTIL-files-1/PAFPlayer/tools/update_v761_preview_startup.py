from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('PAFPlayer.py','releases'),('docs/README.md','docs/backups'),('docs/PAFPlayer_changelog.md','docs/backups')]:
 p=root/raw;base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest()
 target=root/folder/b.name;target.parent.mkdir(exist_ok=True,parents=True)
 while target.exists():n+=1;target=root/folder/(base+f' ({n}).bak')
 b.rename(target)
p=root/'PAFPlayer.py';s=p.read_text(encoding='utf-8-sig');s=s.replace("= 'V760'","= 'V761'").replace('2026-11-25-v760-erase-after-interrupt','2026-11-26-v761-faster-preview-startup')
idx=s.index('def probe_audio_metadata(')
helper='''def track_analysis_cache():
    from PAFPlayer_startup_cache import AnalysisCache
    return AnalysisCache(Path(__file__).resolve().parent / 'runtime/cache/track-analysis')


'''
s=s[:idx]+helper+s[idx:]
start=s.index('    if ffprobe is not None:\n',s.index('def probe_audio_metadata('));end=s.index('\n    duration: float | None = None',start)
old=s[start:end]
body=old.split('    if ffprobe is not None:\n',1)[1]
new='''    if ffprobe is not None:
        from PAFPlayer_startup_cache import tool_signature
        disk_cache = track_analysis_cache()
        disk_key = disk_cache.key(audio_path, ['metadata-v1', tool_signature(ffprobe)])
        disk_value = disk_cache.read('metadata', disk_key)
        if isinstance(disk_value, dict) and isinstance(disk_value.get('format'), dict) and isinstance(disk_value.get('streams', []), list):
            payload = disk_value
        else:
'''+''.join('    '+line+'\n' for line in body.splitlines())+'''            if result.returncode == 0 and isinstance(payload, dict) and isinstance(payload.get('format'), dict):
                disk_cache.write('metadata', disk_key, payload)
'''
s=s[:start]+new+s[end:]
needle='''    def analyze_window(start: float, span: float) -> list[tuple[float, float]]:
'''
replacement='''    from PAFPlayer_startup_cache import tool_signature
    disk_cache = track_analysis_cache()
    disk_key = disk_cache.key(audio_path, ['silence-v1', duration, safe_threshold, safe_min, safe_keep, safe_scan, tool_signature(ffmpeg)])
    disk_value = disk_cache.read('silence', disk_key)
    if (isinstance(disk_value, list) and len(disk_value) == 2
            and isinstance(disk_value[0], (int, float)) and math.isfinite(disk_value[0]) and disk_value[0] >= 0
            and (disk_value[1] is None or (isinstance(disk_value[1], (int, float)) and math.isfinite(disk_value[1]) and disk_value[1] > disk_value[0]))):
        bounds = (float(disk_value[0]), disk_value[1])
        _EDGE_SILENCE_BOUNDS_CACHE[cache_key] = bounds
        return bounds
    analysis_succeeded = True

'''+needle+'''        nonlocal analysis_succeeded
'''
assert s.count(needle)==1;s=s.replace(needle,replacement,1)
needle='''        except (OSError, subprocess.TimeoutExpired):
            return []
        return _silencedetect_intervals(result.stderr or "", span)'''
assert s.count(needle)==1;s=s.replace(needle,'''        except (OSError, subprocess.TimeoutExpired):
            analysis_succeeded = False
            return []
        if result.returncode != 0:
            analysis_succeeded = False
        return _silencedetect_intervals(result.stderr or "", span)''',1)
needle='''    _EDGE_SILENCE_BOUNDS_CACHE[cache_key] = bounds
    return bounds'''
assert s.count(needle)==1;s=s.replace(needle,'''    _EDGE_SILENCE_BOUNDS_CACHE[cache_key] = bounds
    if analysis_succeeded:
        disk_cache.write('silence', disk_key, list(bounds))
    return bounds''',1)
needle='''        self._process = subprocess.Popen(
            [sys.executable, "-B", "-u", str(Path(__file__).resolve()), "--paf-audio-worker"],'''
assert s.count(needle)==1;s=s.replace(needle,'''        from PAFPlayer_startup_cache import audio_worker_command
        self._process = subprocess.Popen(
            audio_worker_command(Path(__file__).resolve(), sys.executable),''',1)
lines=s.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  d=ast.literal_eval(line.split(' = ',1)[1]);d['PAFPlayer_startup_cache']=(root/'src/PAFPlayer_startup_cache.py').read_text(encoding='utf-8-sig');lines[i]='_PAF_BUNDLED_SOURCES = '+repr(d)+'\n'
s=''.join(lines);compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
p=root/'docs/README.md';s=p.read_text(encoding='utf-8-sig');s+='\n\n### V761: faster preview startup\n\nMetadata and edge-silence analysis now survive process restarts in `runtime/cache/track-analysis`, keyed by the audio file identity, size, timestamps, analysis parameters and tool version. Unchanged preview files can reuse analysis while changes invalidate it. Failed scans are not persisted. Original files and trim/gain settings are unchanged.\n\nIsolated audio workers reuse compiled player code under `runtime/cache/worker-code`, keyed by source contents and Python bytecode version. Workers retain the real script path, isolated process and normal command/status protocol. Missing/unreadable caches fall back to source startup. Entries are immutable; no existing cache files are replaced or deleted. Cold first-use analysis still takes time.\n';p.write_text(s,encoding='utf-8')
p=root/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf-8-sig');s=s.replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V761 — November 26, 2026\n\nCache unchanged-file metadata/silence analysis across previews and reuse compiled code for isolated audio-worker startup. [Release notes](../releases/PAFPlayer_v761_faster_preview_startup_release_notes.md).\n',1);p.write_text(s,encoding='utf-8')
print('V761 persistent analysis and compiled worker caches applied with verified backups.')
