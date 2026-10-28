"""Focused, isolated verification; preserve fixtures and write reports in tests/reports."""
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from run_PAFPlayer_tests import install_guards, unique

stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
stage = unique(root/'tests'/'runs'/('remote-v580-'+stamp))
stage.mkdir(parents=True)
work = stage/'work'; work.mkdir()
(stage/'tests').mkdir()
reports = root/'tests'/'reports'
log_path = unique(reports/('remote-v580-checks-'+stamp+'.log'))
result_path = log_path.with_suffix('.json')
files = [root/'PAFPlayer.py', root/'PAFPlayer_monkeymote.py', root/'PAFPlayer_web_workflows.py', root/'PAFPlayer_workflows_ui.py',
         root/'tests'/'test_PAFPlayer_monkeymote_multi.py',
         root/'tests'/'test_PAFPlayer_monkeymote.py',
         root/'tests'/'test_v522_remote_controls.py',
         root/'tests'/'test_PAFPlayer_workflows.py',
         root/'tests'/'test_PAFPlayer_v499_tray.py']
files.extend(root/name for name in ('PAFPlayer_tray_options.py', 'PAFPlayer_steam.py', 'PAFPlayer_tray.py', 'PAFPlayer_tray_hover.py', 'PAFPlayer_tray_machine.py', 'PAFPlayer_remote_overlay.py', 'PAFPlayer_remote_tray.py'))
files.extend(root/'tests'/name for name in ('test_v580_tray_and_steam.py', 'test_v577_remote_save.py', 'test_v503_tray_track_details.py', 'test_v504_tray_machine.py', 'test_v551_tray_icon_matrix.py', 'test_v556_tray_notifications_and_history.py', 'test_v569_tray_api_isolation.py', 'test_v574_remote_floating.py', 'test_v501_floating_title_duration_persistence.py', 'test_v573_lyric_control_character_recovery.py', 'test_v477_floating_lyrics_center.py', 'test_v506_floating_title_persistence.py', 'test_v550_floating_hit_test.py'))
manifest = []
for path in files:
    target = stage/'tests'/path.name if path.parent.name == 'tests' else stage/path.name
    with path.open('rb') as source, target.open('xb') as output:
        shutil.copyfileobj(source, output)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == hashlib.sha256(target.read_bytes()).hexdigest()
    manifest.append({'source': str(path), 'copy': str(target), 'sha256': digest})
for name in ('TEMP', 'TMP', 'LOCALAPPDATA', 'APPDATA'):
    os.environ[name] = str(work)
os.environ['PLAY_AUDIO_FILE_HISTORY_DB'] = str(work/'history.sqlite3')
for name in list(os.environ):
    if name.startswith('LASTFM_') or name == 'PAFPLAYER_DISCORD_WEBHOOK':
        os.environ.pop(name)
tempfile.tempdir = str(work)
sys.path.insert(0, str(stage))
sys.path.insert(0, str(stage/'tests'))
os.chdir(stage)
sys.argv = ['PAFPlayer.py', '--unit-tests']
blocks = install_guards(root/'tests')
suite = unittest.TestSuite()
for name in ('test_v580_tray_and_steam', 'test_v577_remote_save', 'test_PAFPlayer_monkeymote', 'test_PAFPlayer_monkeymote_multi', 'test_v522_remote_controls', 'test_PAFPlayer_v499_tray', 'test_v503_tray_track_details', 'test_v504_tray_machine', 'test_v556_tray_notifications_and_history', 'test_v569_tray_api_isolation', 'test_v574_remote_floating', 'test_v501_floating_title_duration_persistence', 'test_v573_lyric_control_character_recovery', 'test_v477_floating_lyrics_center', 'test_v506_floating_title_persistence'):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
for module_name in ('test_v551_tray_icon_matrix', 'test_v550_floating_hit_test'):
    matrix = importlib.import_module(module_name)
    for name in sorted(vars(matrix)):
        if name.startswith('test_') and callable(getattr(matrix, name)):
            suite.addTest(unittest.FunctionTestCase(getattr(matrix, name)))
workflows = importlib.import_module('test_PAFPlayer_workflows')
suite.addTests(unittest.defaultTestLoader.loadTestsFromNames(['QueueTests', 'SecurityTests'], workflows))
player = importlib.import_module('PAFPlayer')
for name in ('test_v26_shuffle_queue_rotates_played_track_to_tail',
             'test_v12_playlist_previous_walks_real_visit_history',
             'test_v309_fixed_slot_queue_preserves_length_and_duplicates',
             'test_v63_resume_successor_is_captured_before_queue_rotation',
             'test_v91_recent_shuffle_candidate_searches_forward_once_and_avoids_three_hours',
             'test_v91_recent_shuffle_all_recent_has_bounded_fallback',
             'test_v95_web_has_winamp_wawi_style_separate_play_pause_stop_controls',
             'test_v90_web_server_real_ephemeral_roundtrip_and_action_queue'):
    suite.addTest(player.PlayWaveFileTests(name))
with log_path.open('x', encoding='utf-8') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    summary = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   skipped=len(result.skipped), successful=result.wasSuccessful(),
                   fixture_copies=manifest, blocked_writes=blocks, log=str(log_path))
with result_path.open('x', encoding='utf-8') as output:
    json.dump(summary, output, indent=2)
print(json.dumps({k:v for k,v in summary.items() if k not in ('fixture_copies','blocked_writes')}, indent=2))
if not result.wasSuccessful():
    print(log_path.read_text(encoding='utf-8')[-16000:])
raise SystemExit(0 if result.wasSuccessful() else 1)
