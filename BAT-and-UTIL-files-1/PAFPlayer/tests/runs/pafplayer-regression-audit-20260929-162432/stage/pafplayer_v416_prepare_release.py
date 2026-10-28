from pathlib import Path
from datetime import datetime
import hashlib
import json
import re

from pafplayer_v416_edit import unique

root = Path(__file__).resolve().parent
source = root / 'play_audio_file.py'
payload = source.read_bytes()
compile(payload, str(source), 'exec')
versioned = unique(root / 'play_audio_file_v416_timestamped_timelines_and_external_media.py')
versioned.write_bytes(payload)
assert versioned.read_bytes() == payload
baseline = root / 'play_audio_file.py.bak.202609141603.replaced-by-chatgpt.bak'
report = json.loads((root / 'pafplayer_v416_final_regression_audit (3).json').read_text())
manifest = {
    'version': 'V416', 'build': '2026-09-20-v416-timelines-todos-external-media',
    'prepared_at': datetime.now().isoformat(),
    'source': str(source), 'versioned_source': str(versioned),
    'sha256': hashlib.sha256(payload).hexdigest(),
    'baseline_source': str(baseline), 'baseline_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
    'installed_before_sha256': 'b1f0a7503beb92af39805cc60f02495a4f6503c8cb3a8aaf78aee1d5e6792000',
    'focused_tests_passed': 56,
    'historical_suite': {'run': report['run'], 'failures': len(report['failures']), 'errors': len(report['errors']),
                         'original_v414_failures': 51, 'original_v414_errors': 5,
                         'additional_full_suite_failure': 'test_v88_probe_metadata_exposes_original_artist_composer_and_raw_tags_from_one_probe',
                         'additional_failure_isolated_rerun': 'passed', 'report': 'pafplayer_v416_final_regression_audit (3).json'},
    'native_and_decoder_validation': 'pafplayer_v416_validation (2).json',
    'native_clock_stress': 'pafplayer_v416_clock_stress.json',
    'external_media_checks': {'windows_smtc_native': 'passed outside sandbox', 'windows_audio_sessions': 'passed',
                             'helper_shutdown': 'passed', 'player_pause_resume_integration': 'passed',
                             'actual_15_second_ffmpeg_gain_envelope': 'passed',
                             'interactive_youtube_winamp_cycle': 'not performed'},
    'release_notes': str(root / 'play_audio_file_v416_release_notes.md'),
}
destination = unique(root / 'pafplayer_v416_release_manifest.json')
destination.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps({'snapshot': str(versioned), 'manifest': str(destination), 'sha256': manifest['sha256']}))
