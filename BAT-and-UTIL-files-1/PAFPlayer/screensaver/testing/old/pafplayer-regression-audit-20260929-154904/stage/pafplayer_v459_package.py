"""Package the tested song-ending fix, carrying forward V458 retention repairs."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / 'pafplayer-regression-audit-20260928-132521'
BASELINE = ROOT / 'pafplayer-regression-audit-20260928-130950'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def failures(reports):
    result = {}
    for report in reports:
        assert not any(report.get(key) for key in ('import_error', 'timeout', 'missing_report')), report
        for entry in report['entries']:
            if entry['outcome'] in ('failure', 'error', 'subtest-failure'):
                result[entry.get('parent_test') or entry['test']] = entry
    return result


summary = json.loads((AUDIT / 'summary.json').read_text())
reports = json.loads((AUDIT / 'results.json').read_text())
remaining = failures(reports)
previous = failures(json.loads((BASELINE / 'results.json').read_text()))
assert set(remaining) <= set(previous), 'New non-passing methods since V458'
for module, count in (('test_PAFPlayer_v458', 21), ('test_PAFPlayer_v459', 11)):
    report = next(row for row in reports if row['module'] == module)
    assert report['successful'] and report['count'] == count
    assert all(entry['outcome'] == 'pass' for entry in report['entries'])
assert digest(ROOT / 'PAFPlayer.py') == digest(AUDIT / 'stage/PAFPlayer.py') == digest(ROOT / 'PAFPlayer_v459_complete_song_endings.py')

before = ast.parse((ROOT / 'PAFPlayer_v458_memory_and_regressions.py').read_text(encoding='utf-8-sig'))
after = ast.parse((ROOT / 'PAFPlayer.py').read_text(encoding='utf-8-sig'))
assert len(before.body) == len(after.body)
changed = []
for old, new in zip(before.body, after.body):
    if ast.dump(old) != ast.dump(new):
        changed.append(new.name if isinstance(new, ast.FunctionDef) else new.targets[0].id)
assert changed == ['PLAYER_BUILD_ID', 'PROGRAM_VERSION', 'PROGRAM_RELEASE_LABEL', 'matrixmixer_inspired_ffmpeg_command'], changed

notes = f'''# PAFPlayer V459 — September 28, 2026

## Complete song endings

Fixed early endings during ordinary automatic next-song transitions in the
buffered/native playback path. FFmpeg previously received a source-duration
limit after its input, where it limited output time after tempo processing.
At 0.9× speed this discarded roughly the last 10% of a song. The running player's
decoder command was confirmed to use that combination. At faster speeds, the
same mistake could play beyond an explicitly bounded source segment.

The duration limit now applies to input decoding, before tempo processing.
Existing seek positions, ReplayGain, channel mixing, sample formats and device
buffer-drain behavior are preserved. Relative to V458, the only production
function changed is `matrixmixer_inspired_ffmpeg_command`, plus release metadata.

## Actual decoded audio

A generated 50-second recording has a distinct 1429-Hz tone in its final second.
The test decodes actual PCM using the production FFmpeg command without opening
an audio device. At 0.9×, V458 emitted 50.000 seconds and lost the ending tone;
V459 emits 55.551 seconds and preserves it (55.556 expected). At 0.5×, the output
changed from 50.000 to 99.982 seconds and the ending tone is retained. Normal and
faster speeds also preserve the ending. Seeking into the final ten seconds works,
and a faster bounded segment stops at its requested source end.

Eleven new regression tests pass: eight real decode scenarios, including the
7.1/96-kHz/24-bit output format, and three completion/drain guards. These verify
that decoder EOF does not report completion while PCM is still draining, natural
close does not reset the device, and all output endpoints finish before advancing.
No production drain logic needed changing. Actual listening on the user's audio
hardware was not performed, and the running player was not interrupted.

## Includes the completed memory repairs

V458's cover cache limits (24 entries and 64 MiB), coalesced popup updates,
partial-console-write repair, legacy launcher synchronization, history-report
repair, and on-demand runtime diagnostics are included. The accelerated cover
workload stopped growing at 24 MiB instead of retaining 512 MiB; stalled popup
title work stayed at one command instead of 100,000. Sampled rendered frames were
identical to the baseline. Full measurements and limits are in the included
[V458 release notes](PAFPlayer_v458_release_notes.md). Hours of real playback with
console, artwork popup and floating lyrics together still require observation
after restart; the accelerated measurements do not certify every FPS slowdown.

## Full regression run

**{summary['tests_run']} distinct tests: {summary['outcomes']['pass']} passed,
{summary['outcomes'].get('failure', 0)} failed assertions, and
{summary['outcomes'].get('error', 0)} errors. The complete historical suite is not green.**

All 32 new V458/V459 tests pass. No previously passing method became non-passing
relative to the full V458 audit. The {len(remaining)} remaining historical methods
already failed before these releases; they include UI/render/source contracts
and old version-identity expectations. They are tracked for reconciliation,
not blanket-skipped or assumed harmless. The runner reports a failure exit code.
Each remaining method is listed below; JSON results contain the tracebacks.

Run `python -B -X utf8 run_PAFPlayer_tests.py` for the complete isolated suite.
Run `python -B -X utf8 pafplayer_v459_decode_check.py PAFPlayer.py NEW_DIRECTORY`
for the 50-second decode experiment; its output directory must not already exist.

## Installation

Restart PAFPlayer to load V459. This release updates `C:\\BAT\\PAFPlayer.py` after
a verified sibling backup; V458 already updated the compatibility launcher.
The ZIP includes exact tested inputs, release notes, results and measurements.
The installation report records every changed path and checksum.

## Remaining historical failures

'''
notes += '\n'.join(f'- `{name}` ({entry["outcome"]})' for name, entry in sorted(remaining.items())) + '\n'
for folder in (ROOT, ROOT / 'docs/PAFPlayer'):
    with (folder / 'PAFPlayer_v459_release_notes.md').open('x', encoding='utf-8') as stream:
        stream.write(notes)

files = {}
for item in json.loads((AUDIT / 'manifest.json').read_text()):
    staged = Path(item['staged'])
    assert digest(staged) == item['sha256'], staged
    files[staged.name] = staged
for name in ('paf.bat', 'run_PAFPlayer_tests.py', 'pafplayer_v458_soak.py',
             'pafplayer_v459_decode_check.py', 'PAFPlayer_v458_release_notes.md',
             'PAFPlayer_v459_release_notes.md', 'PAFPlayer_TODO.md', 'PAFPlayer_changelog.md'):
    files[name] = ROOT / name
for name in ('results.json', 'summary.json', 'manifest.json'):
    files['validation/' + name] = AUDIT / name
for name in ('pafplayer-v457-soak-20260927-v2.json', 'pafplayer-v458-soak-20260927.json'):
    files['validation/' + name] = ROOT / name
for version, folder in ((458, 'pafplayer-v458-eof-reproduction-20260928'),
                        (459, 'pafplayer-v459-eof-verification-20260928')):
    files[f'validation/v{version}-decode-results.json'] = ROOT / folder / 'results.json'
archive = ROOT / 'releases/PAFPlayer-v459.zip'
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
    for name, path in sorted(files.items()):
        package.write(path, name)
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None
    for name, path in files.items():
        assert hashlib.sha256(package.read(name)).hexdigest() == digest(path), name
manifest = {'version': 'V459', 'archive_sha256': digest(archive),
            'files': {name: digest(path) for name, path in sorted(files.items())},
            'validation': summary, 'new_regressions_against_v458': [],
            'production_ast_changes': changed}
with (ROOT / 'releases/PAFPlayer-v459-manifest.json').open('x', encoding='utf-8') as stream:
    json.dump(manifest, stream, indent=2)
print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size,
                  'summary': summary, 'remaining_historical': len(remaining)}, indent=2))
