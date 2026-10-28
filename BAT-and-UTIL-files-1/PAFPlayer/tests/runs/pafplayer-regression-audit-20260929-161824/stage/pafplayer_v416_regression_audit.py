"""Run the embedded historical suite and record compact, baseline-comparable failures."""
import io
import json
import sys
import unittest
from pathlib import Path
import play_audio_file as p
from pafplayer_v416_edit import unique

sys.argv.append('--unit-tests')
stream = io.StringIO()
suite = unittest.defaultTestLoader.loadTestsFromTestCase(p.PlayWaveFileTests)
result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
summary = {'run': result.testsRun,
           'failures': [{'test': test.id(), 'error': error.splitlines()[-1][:500]} for test, error in result.failures],
           'errors': [{'test': test.id(), 'error': error.splitlines()[-1][:500]} for test, error in result.errors]}
path = unique(Path(__file__).with_name('pafplayer_v416_final_regression_audit.json'))
path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'report': str(path)}))
