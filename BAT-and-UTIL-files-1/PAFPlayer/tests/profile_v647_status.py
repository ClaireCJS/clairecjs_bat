"""Isolated read-only measurements of the periodic status preparation path."""
import cProfile
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import pstats
import statistics
import sys
import tempfile
import time

from run_PAFPlayer_tests import install_guards, unique

ROOT = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT/'PAFPlayer.py'
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
stage = unique(ROOT/'tests/runs'/('status-v647-'+stamp)); stage.mkdir(parents=True)
with (stage/'PAFPlayer.py').open('xb') as f: f.write(source.read_bytes())
for key in ('TEMP', 'TMP', 'APPDATA', 'LOCALAPPDATA'): os.environ[key] = str(stage)
os.environ['PLAY_AUDIO_FILE_HISTORY_DB'] = str(stage/'history.sqlite3')
tempfile.tempdir = str(stage)
sys.path.insert(0, str(stage)); sys.argv = ['PAFPlayer.py', '--unit-tests']; os.chdir(stage)
blocks = install_guards(ROOT/'tests')
import PAFPlayer as app

def read_titles_old():
    return (int(app.load_player_settings(read_only=True).get('ConsoleTitleStyle', 1)),
            int(app.load_player_settings(read_only=True).get('ConsoleTitleContent', 1)))

timings=[]
for _ in range(20):
    started=time.perf_counter(); titles=read_titles_old();timings.append((time.perf_counter()-started)*1000)
profile=cProfile.Profile();profile.enable()
for _ in range(5): read_titles_old()
profile.disable()
text=io.StringIO();pstats.Stats(profile,stream=text).strip_dirs().sort_stats('cumulative').print_stats(20)
report=unique(ROOT/'tests/reports'/('v647-status-profile-'+app.PROGRAM_VERSION+'-'+stamp+'.json'))
with report.with_suffix('.txt').open('x',encoding='utf-8') as f:f.write(text.getvalue())
summary=dict(version=app.PROGRAM_VERSION,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             double_settings_read_median_ms=statistics.median(timings),max_ms=max(timings),
             settings_count=len(app.PLAYER_SETTING_DEFAULTS),blocks=blocks)
with report.open('x',encoding='utf-8') as f:json.dump(summary,f,indent=2)
print(json.dumps(summary));print(text.getvalue());print(report)
