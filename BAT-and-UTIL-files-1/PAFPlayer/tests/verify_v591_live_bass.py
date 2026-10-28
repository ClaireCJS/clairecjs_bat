"""Run locked-bass and related playback checks in retained, guarded staging."""
from datetime import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest import mock

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from run_PAFPlayer_tests import install_guards, unique

stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
stage = unique(root / 'tests/runs' / ('bass-v591-' + stamp))
stage.mkdir(parents=True)
(stage / 'tests').mkdir()
work = stage / 'work'; work.mkdir()
files = ['PAFPlayer.py', 'tests/test_v590_locked_bass.py', 'tests/test_v591_live_bass.py', 'tests/test_v521_realtime_controls.py', 'tests/test_v485_bass_controls.py',
         'tests/test_v548_locked_bass.py', 'tests/test_v552_channels_and_locked_bass.py',
         'tests/probe_v482_track_renderer.py', 'tests/test_play_audio_file_v402_audio_ui.py']
copies = []
for name in files:
    src, dst = root / name, stage / name
    with src.open('rb') as read, dst.open('xb') as write:
        shutil.copyfileobj(read, write)
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    assert sha == hashlib.sha256(dst.read_bytes()).hexdigest()
    copies.append({'source': str(src), 'copy': str(dst), 'sha256': sha})
for name in ('APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP'):
    os.environ[name] = str(work)
os.environ['PLAY_AUDIO_FILE_HISTORY_DB'] = str(work / 'history.sqlite3')
os.environ['OPENBLAS_NUM_THREADS'] = '1'
for name in list(os.environ):
    if name.startswith('LASTFM_') or name == 'PAFPLAYER_DISCORD_WEBHOOK':
        os.environ.pop(name)
tempfile.tempdir = str(work)
os.chdir(stage)
sys.path[:0] = [str(stage), str(stage / 'tests')]
sys.argv = ['PAFPlayer.py', '--unit-tests']
blocks = install_guards(root / 'tests')
app = importlib.import_module('PAFPlayer')
sys.modules['play_audio_file'] = app
steam = importlib.import_module('PAFPlayer_steam')
suite = unittest.TestSuite()
for name in ('test_v590_locked_bass', 'test_v591_live_bass', 'test_v521_realtime_controls', 'test_v485_bass_controls'):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
for module_name in ('test_v548_locked_bass', 'test_v552_channels_and_locked_bass'):
    module = importlib.import_module(module_name)
    for name in sorted(vars(module)):
        if name.startswith('test_') and callable(getattr(module, name)):
            suite.addTest(unittest.FunctionTestCase(getattr(module, name)))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(importlib.import_module('test_play_audio_file_v402_audio_ui').WorkerTests))
names = [name for name in dir(app.PlayWaveFileTests) if name.startswith('test_v82_replaygain_')]
names += ['test_v230_mminspo_accumulates_short_pipe_reads_into_real_audio_blocks', 'test_v489_bass_lock_web_setting_persists_and_republishes',
          'test_seek_restarts_ffplay_at_requested_offsets',
          'test_v228_mminspo_waveformatextensible_masks_and_pcm_command',
          'test_v97_aresample_is_last_stage_of_single_filter_chain',
          'test_v369_stereo_waveout_format_and_command',
          'test_v90_web_server_real_ephemeral_roundtrip_and_action_queue']
for name in names:
    cases = [value for value in vars(app).values() if isinstance(value, type) and issubclass(value, unittest.TestCase) and hasattr(value, name)]
    assert len(cases) == 1, (name, cases)
    suite.addTest(cases[0](name))
log = unique(root / 'tests/reports' / ('v591-bass-checks-' + stamp + '.log'))
with log.open('x', encoding='utf-8') as output, \
     mock.patch.object(steam, 'get_monitor', return_value=NS(visualizer_fps=lambda fps: fps, hud_notice=lambda: '')):
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
summary = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
               skipped=len(result.skipped), successful=result.wasSuccessful(),
               copies=copies, blocked_writes=blocks, log=str(log))
with log.with_suffix('.json').open('x', encoding='utf-8') as output:
    json.dump(summary, output, indent=2)
print(json.dumps({k:v for k,v in summary.items() if k not in ('copies','blocked_writes')}, indent=2))
for case, detail in result.failures + result.errors:
    print(str(case), detail[:2500])
raise SystemExit(0 if result.wasSuccessful() else 1)
