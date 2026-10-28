"""Package the exact tested V458 source and preserve full, non-green results."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / 'pafplayer-regression-audit-20260928-130950'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


summary = json.loads((AUDIT / 'summary.json').read_text())
reports = json.loads((AUDIT / 'results.json').read_text())
baseline = json.loads((ROOT / 'pafplayer-regression-audit-20260927-145105/reconciled-results.json').read_text())
prior_failures = {row['test'] for row in baseline['failures']}
remaining = {}
for report in reports:
    assert not report.get('import_error') and not report.get('timeout') and not report.get('missing_report'), report['module']
    for entry in report['entries']:
        if entry['outcome'] in ('failure', 'error', 'subtest-failure'):
            remaining[entry.get('parent_test') or entry['test']] = entry
assert set(remaining) <= prior_failures, 'New failure compared with audited V457'
assert digest(ROOT / 'PAFPlayer.py') == digest(AUDIT / 'stage/PAFPlayer.py') == digest(ROOT / 'PAFPlayer_v458_memory_and_regressions.py')
new_tests = next(report for report in reports if report['module'] == 'test_PAFPlayer_v458')
assert new_tests['successful'] and new_tests['count'] == 21
old = json.loads((ROOT / 'pafplayer-v457-soak-20260927-v2.json').read_text())
new = json.loads((ROOT / 'pafplayer-v458-soak-20260927.json').read_text())
assert old['sampled_frame_sha256'] == new['sampled_frame_sha256']
notes = f'''# PAFPlayer V458 — September 28, 2026

## Changes

Cover artwork previously remained cached for every visited track. The cache now
keeps at most 24 entries and 64 MiB of compressed payload, evicting matching source
metadata too. Cache hits refresh recency; missing-art lookups are bounded; a cover
larger than the cache budget still displays without being retained in this cache.

Popup titles and loaded artwork now use one latest-value mailbox per kind.
Obsolete loader results are discarded before enqueueing. Existing lyric
coalescing remains in place, and the Tk command loop yields after 32 commands.
Ordered control requests remain queued normally. No renderer colors, glyphs,
compositing equations, lyric polling rates, or audio parameters were changed.

Also fixed the history-report crash when progress bars are disabled, completed
partial console writes without repeating accepted prefixes, and synchronized
release metadata. The legacy `play_audio_file.py` now executes its sibling
`PAFPlayer.py`, preventing old launchers/tests from silently loading V447.
The canonical program retains its self-contained bundled feature modules.

## Retention and rendering evidence

| Accelerated workload | V457 | V458 |
|---|---:|---:|
| 512 tracks, independent 1-MiB covers | 512 MiB cached | 24 MiB cached |
| 100,000 titles with GUI consumer stalled | 100,000 commands | 1 command |
| 2,400 moving frames, first 400 median | {old['renderer'][0]['median_ms']} ms | {new['renderer'][0]['median_ms']} ms |
| Same workload, final 400 median | {old['renderer'][-1]['median_ms']} ms | {new['renderer'][-1]['median_ms']} ms |

The workload used 200 columns × 32 rows, Twin DRCS, Signal Aurora, background
and bar artwork, detail 9, blend 1, and 64% bar opacity. Sampled complete frame
payloads were byte-identical between releases. Renderer memory reached a stable
working range in the measured run. Full raw measurements and the reproducible
soak script are included. These tests reproduced two retention defects; they do
not prove that those defects explain every observed long-session slowdown.

The accelerated test does not replace hours of real playback with console,
artwork popup, and floating lyrics together. It excludes actual Tk painting and
terminal transport. Real audio stuttering and end-to-end 60 FPS are not certified.
An older high-memory Python process exited before its identity could be verified;
its memory consumption is not used as proof about PAFPlayer.

## Full regression run

**{summary['tests_run']} distinct tests: {summary['outcomes']['pass']} passed,
{summary['outcomes'].get('failure', 0)} failed assertions, and
{summary['outcomes'].get('error', 0)} errors. The full historical suite is not green.**

All 21 new V458 tests pass, including concurrent cache users, oversized artwork,
latest-title/artwork behavior, partial writes, the legacy entry point, native
memory counters, and a real local HTTP diagnostics request. All current V456
workflow/release/integration tests pass. The existing native console-row behavior
tests pass. Compared with the audited V457 run, none of the previously passing
test methods became non-passing. Confirmed defects were repaired; 26 historical
expectations/fixtures were reconciled with already-approved behavior, including
wildcard learned tags, literal duplicate playlist slots, current arrows, the
loudness offset/deadband/fallback, audible media detection, and startup source
acknowledgement. Tests were not blanket-skipped or marked expected failures.

The remaining {len(remaining)} methods already failed in the V457 audit. They
include old HUD and GUI/source-string contracts, historical renderer comparisons,
rollback-era console helpers, and frozen version/whole-program identity checks.
Their age does not prove every failure harmless; full reconciliation remains
tracked in TODO. Each remaining method is listed below and its traceback remains
in the included JSON. The test runner returns a failure exit status accordingly.

Run `python -B -X utf8 run_PAFPlayer_tests.py` from the project/release root.
It discovers all 671 embedded methods plus standalone player modules, tests
SHA-verified copies in isolated staging, and preserves results and fixtures.
The separate filelist-generator project's pytest configuration is untouched.

## On-demand diagnosis after restart

Open `http://127.0.0.1:666/api/runtime-diagnostics` for process private/working-set
memory, uptime, thread count, artwork payload/count, popup backlog, function-cache
sizes, and collection counts. The endpoint collects counters only when requested;
it does not walk the heap, force garbage collection, or add a playback poller.
It reports aggregate counts without track filenames. An already running process
must be restarted to load these fixes, even if its version label already says V458.

## Publishing

The release ZIP contains the tested canonical program, compatibility launcher,
test inputs/runner, diagnostics/stress evidence, and documentation. Installation
updates `C:\\BAT\\PAFPlayer.py` and `C:\\BAT\\play_audio_file.py` after verified
sibling backups. `paf.bat` already targets the canonical program and is unchanged.
The installation report records each affected C:\\BAT path and checksum.

The next active investigation is the reported loss of approximately the final
five seconds of songs. V458 does not claim to fix that separate issue.

## Remaining historical failures

'''
notes += '\n'.join(f'- `{name}` ({entry["outcome"]})' for name, entry in sorted(remaining.items())) + '\n'
for folder in (ROOT, ROOT / 'docs/PAFPlayer'):
    with (folder / 'PAFPlayer_v458_release_notes.md').open('x', encoding='utf-8') as stream:
        stream.write(notes)
inputs = json.loads((AUDIT / 'manifest.json').read_text())
files = {}
for item in inputs:
    staged = Path(item['staged'])
    assert digest(staged) == item['sha256'], 'Test modified a packaged input: ' + staged.name
    files[staged.name] = staged
files['PAFPlayer.py'] = ROOT / 'PAFPlayer.py'
files['PAFPlayer_v458_memory_and_regressions.py'] = ROOT / 'PAFPlayer_v458_memory_and_regressions.py'
for name in ('paf.bat', 'run_PAFPlayer_tests.py', 'pafplayer_v458_soak.py', 'PAFPlayer_v458_release_notes.md', 'PAFPlayer_TODO.md', 'PAFPlayer_changelog.md'):
    files[name] = ROOT / name
for name in ('results.json', 'summary.json', 'manifest.json'):
    files['validation/' + name] = AUDIT / name
for name in ('pafplayer-v457-soak-20260927-v2.json', 'pafplayer-v458-soak-20260927.json'):
    files['validation/' + name] = ROOT / name
archive = ROOT / 'releases/PAFPlayer-v458.zip'
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
    for name, path in sorted(files.items()):
        package.write(path, name)
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None
    for name, path in files.items():
        assert hashlib.sha256(package.read(name)).hexdigest() == digest(path), name
manifest = {'version': 'V458', 'archive_sha256': digest(archive),
            'files': {name: digest(path) for name, path in sorted(files.items())},
            'validation': summary, 'new_regressions_against_v457': []}
with (ROOT / 'releases/PAFPlayer-v458-manifest.json').open('x', encoding='utf-8') as stream:
    json.dump(manifest, stream, indent=2)
print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size, 'summary': summary, 'remaining_historical': len(remaining)}, indent=2))
