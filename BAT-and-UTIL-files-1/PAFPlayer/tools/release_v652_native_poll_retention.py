"""Publish the tested snapshot while preserving concurrent newer player work."""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from prepare_v642_artwork_chrome import ROOT, write, unique

def read_report(name): return json.loads((ROOT/'tests/reports'/name).read_text(encoding='utf8'))
def names(report, key): return {name for name, traceback in report[key]}

native=read_report('native-checks-V652-20261111-062531.json')
native_before=read_report('native-checks-V651-20261111-062824.json')
broad=read_report('pipeline-regressions-V652-20261111-063118.json')
broad_before=read_report('pipeline-regressions-V651-20261111-062821.json')
assert native['tests']==107 and native_before['tests']==98
assert broad['tests']==broad_before['tests']==188
for key in ('failures','errors'):
    assert names(native,key)==names(native_before,key)
    assert names(broad,key)==names(broad_before,key)
assert len(native['failures'])==2 and not native['errors']
assert len(broad['failures'])==11 and len(broad['errors'])==1
tested=Path(native['stage'])/'PAFPlayer.py';data=tested.read_bytes()
digest=hashlib.sha256(data).hexdigest()
assert digest==native['source_sha256']==broad['source_sha256']=='ae9aaea9f3cc9a95ce9d0e99e7597d49867a2fc702cefc865e922b44417422db'
assert data==(Path(broad['stage'])/'PAFPlayer.py').read_bytes()

def functions(text):
    return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(text).body
            if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
old=functions(tested.read_text(encoding='utf8'));active=functions((ROOT/'PAFPlayer.py').read_text(encoding='utf8'))
for name in ('_external_audio_probe_api','probe_external_audio_sessions','_windows_process_memory_api',
             'paf_runtime_diagnostics_snapshot','_console_cursor_info_type','set_console_cursor_visible',
             '_windows_last_input_info_type','windows_last_input_tick'):
    assert old[name]==active[name],name

release=unique(ROOT/'releases/PAFPlayer_v652_native_poll_retention.py')
with release.open('xb') as f:f.write(data)
assert release.read_bytes()==data
notes=unique(release.with_name(release.stem+'_release_notes.md'))
notes_text=f'''# PAFPlayer V652 — native polling memory retention and cleanup stalls

Released November 11, 2026. SHA-256: `{digest}`.

The remaining tiny visualizer hangs were investigated beyond rendering itself.
Two roughly 270–290 ms diagnostic delays in a V650 live trace coincided with
generation-2 garbage collection. Those are HTTP sampling delays, not measured
frame durations. The same live process subsequently reported about 6.25 GB of
private memory after 5.4 hours, compared with about 1.42 GB early in the session.
These observations motivated isolated allocation checks, not a claim that all
growth or every hitch had one cause.

## Root cause and fix

Repeated external-audio polling recreated GUID/PROPERTYKEY classes and native
function signatures. Python ctypes retains pointer and callback signature types
in process-wide caches, so these definitions and their object graphs survived
ordinary garbage collection. Steam process enumeration and diagnostic memory
polling had the same structure-type retention problem. Casting owning COM
pointer wrappers also created disposable self-reference cycles on each call.

V652 reuses those native definitions and private DLL bindings. COM apartments,
interfaces, handles, process records, and memory values still belong to each
individual poll and are acquired/read/released as before. It casts the numeric
COM address while retaining the owning argument during the call. Steam reuses
one path buffer per enumeration. Cursor visibility and idle-input polling reuse
their small structure definitions instead of creating collectible class graphs.

No garbage collector policy, audio processing, frame target, rendering precision,
terminal encoding, configuration ID, or polling cadence changed. The playback
owner and artwork-popup implementations are AST-identical to the V651 snapshot.
The native monitor continues to read external playback; it sends no playback or
volume commands. V651's idle-art controls and session-error display are preserved.

## Measurements and validation

The benchmark used the then-current V651 source, then the fixed candidate and
current V653 source after another chat advanced the working file. The changed
native functions are retained in that newer source.

| Isolated workload | V651 | V652 |
| --- | ---: | ---: |
| New retained pointer/function types, 20 audio polls | 340 | 0 |
| Cyclic garbage, 20 audio polls | 4,877 objects | 17 objects |
| New retained pointer types, 100 diagnostics | 100 | 0 |
| New retained pointer types, 20 Steam polls | 20 | 0 |
| Cyclic garbage, 100 cursor visibility calls | 1,100 objects | 0 |

The accelerated soak performed 500 real read-only audio polls, 100 diagnostic
reads and 20 Steam enumerations in isolated processes with normal automatic GC.
Both versions returned 500 known audio samples. After cleanup, V651 retained
129,197 additional tracked objects and 14,049,280 additional private bytes.
V652 retained two additional tracked objects; private bytes decreased by 503,808.
This verifies the targeted retention fix, not a full-player multi-hour soak or
a guaranteed FPS improvement. Warm artwork-render cost remained about 1.8 ms
in the synthetic fixture; rendering itself was not modified in this release.

- [V651 allocation probe](../tests/reports/pipeline-gc-V651-20261111-062028.json)
- [Fixed candidate allocation probe](../tests/reports/pipeline-gc-V651-20261111-062303.json)
- [Current V653 allocation probe](../tests/reports/pipeline-gc-V653-20261111-063118.json)
- [V651 soak](../tests/reports/native-soak-V651-20261111-062528.json)
- [V652 soak](../tests/reports/native-soak-V652-20261111-062525.json)
- [Original live sampling](../tests/reports/v648-thread-stacks-20261111-005959.json)

All nine new regression tests pass. The 107-test native/Steam/media/retention
selection has 105 passes and the same two old media-coordinator failures as the
98-test V651 baseline. The 188-test render/karaoke/transport selection has 176
passes, 11 old failures and one old source-contract error, matching V651 exactly.
Python compilation, 27 bundled-source comparisons and eight generated JavaScript
syntax checks pass. This is not an all-green full-suite claim.

The previous combined GUI harness aborted on both versions with Tk's wrong-thread
cleanup diagnostic. The new test runner collects destroyed Tk fixture cycles on
their main owner thread before starting the next test. That test-only cleanup
allowed both 188-test comparisons to finish; production GC behavior is unchanged.
An initial missing Steam source fixture in the new runner was corrected; the
original failed reports remain retained.

- [V652 focused/relevant checks](../tests/reports/native-checks-V652-20261111-062531.json)
- [V651 matching baseline](../tests/reports/native-checks-V651-20261111-062824.json)
- [V652 broad selection](../tests/reports/pipeline-regressions-V652-20261111-063118.json)
- [V651 broad baseline](../tests/reports/pipeline-regressions-V651-20261111-062821.json)

## Restart and live verification

Restart the player to load the fixes and release the old process's retained
types. The active PAFPlayer.py has advanced independently to V653 and contains
these changes; this immutable V652 copy preserves the exact tested performance
change. Keep console karaoke, artwork popup and floating lyrics running. Check
lyric-gap resizes and normal playback for remaining hitches; observe memory
over several hours using occasional `/api/runtime-diagnostics` reads.
`tests/probe_v648_thread_stacks.py` can collect a bounded local stack/GC trace.
Do not infer frame latency from HTTP request latency alone.

Live visual smoothness and multi-hour whole-player memory stability after restart
remain unverified. The formerly running V650 process was not stopped or altered.
Other non-hot dynamic native types remain outside this focused change; this does
not claim every possible allocation or leak in the application is removed.

## Files and safety

Replaced files received verified sibling backups, archived in their designated
folders. Prior release artifacts were preserved. No files were permanently
deleted. Root audit results and every operation-owned artifact are recorded in
[the affected-path manifest](../tests/reports/v652-change-manifest.json).
`play_audio_file.py` was not changed. No literal C:\\BAT paths changed.
'''
write(notes.relative_to(ROOT),notes_text)

p=ROOT/'docs/performance-v519.md';s=p.read_text(encoding='utf8')
assert '## V652 native polling retention' not in s
write(p.relative_to(ROOT),s+'''

## V652 native polling retention

Follow-up on the tiny remaining hangs found full-GC events coincident with two
270–290 ms diagnostic delays and substantial live memory growth. Isolated tests
of the current V651 source demonstrated retained ctypes class/signature graphs
from external-audio, Steam and diagnostic polling. V652 caches those definitions,
avoids COM pointer self-cycles, and reuses cursor/idle-input structure types.
It leaves polling cadence, automatic GC, audio and rendering behavior intact.

After 500 audio polls, 100 diagnostics and 20 Steam polls, V651 retained about
129,000 extra tracked objects and 14 MB after collection; V652 retained two extra
objects and no memory increase. All nine new tests pass. Both relevant existing
selections match their baseline failures; compilation, 27 bundle comparisons and
eight web-script checks pass. The newer V653 working source retains the fixes.
Restart is required to load them and discard allocations in the old process.
Whole-player multi-hour stability and visible smoothness still need verification.
[Measurements, limitations, test results and procedure](../releases/PAFPlayer_v652_native_poll_retention_release_notes.md).
''')
p=ROOT/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf8')
assert '## V652 ' not in s and '## V651 ' in s
entry='''## V652 — November 11, 2026

Fix steadily retained ctypes pointer/signature definitions in external-audio,
Steam and diagnostic polling; avoid disposable COM pointer cycles and reuse
cursor/idle-input types. The isolated repeated-poll workload went from roughly
129,000 extra retained objects to two, without changing GC policy or rendering.
Nine new tests pass; 107-test and 188-test selections match the old failures in
their V651 baselines. The changes are preserved in the newer V653 working file.
Live smoothness and a multi-hour playback soak remain pending restart.
[Release notes](../releases/PAFPlayer_v652_native_poll_retention_release_notes.md).

'''
s=s.replace('## V651 ',entry+'## V651 ',1);write(p.relative_to(ROOT),s)
p=ROOT/'docs/README.md';s=p.read_text(encoding='utf8')
match=re.search(r'Current release: \*\*V(\d+)\*\*[^\n]*\n\[[^\n]*\n',s)
if match and int(match[1])<=652:
    replacement='''Current release: **V652** — fix memory retention in native polling that can contribute to periodic visualizer hangs.
[Measurements, limitations, and verification](performance-v519.md#v652-native-polling-retention).
The active working source has advanced separately to V653 and retains these fixes.
'''
    write(p.relative_to(ROOT),s[:match.start()]+replacement+s[match.end():])

# Audit/tidy the required roots without touching active implementation inputs.
moves=[]
for backup in ROOT.glob('PAFPlayer.py.bak.*.replaced-by-chatgpt*.bak'):
    target=unique(ROOT/'releases'/backup.name);expected=hashlib.sha256(backup.read_bytes()).hexdigest()
    assert ROOT in backup.resolve().parents and ROOT in target.resolve().parents
    backup.rename(target);assert hashlib.sha256(target.read_bytes()).hexdigest()==expected
    moves.append({'from':str(backup),'to':str(target),'status':'moved','sha256':expected})
cache=ROOT/'__pycache__'
if cache.exists():
    target=unique(ROOT/'backups'/('__pycache__-'+datetime.now().strftime('%Y%m%d%H%M')))
    assert ROOT in cache.resolve().parents and ROOT in target.resolve().parents
    before={str(p.relative_to(cache)):hashlib.sha256(p.read_bytes()).hexdigest() for p in cache.rglob('*') if p.is_file()}
    cache.rename(target)
    assert before=={str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}
    moves.append({'from':str(cache),'to':str(target),'status':'moved','files':before})
audit=unique(ROOT/'tests/reports/v652-publication.json')
summary=dict(release=str(release),sha256=digest,notes=str(notes),active_source_version='V653',
    active_source_sha256=hashlib.sha256((ROOT/'PAFPlayer.py').read_bytes()).hexdigest(),native_functions_preserved=True,
    focused_tests=107,new_tests=9,broad_tests=188,baseline_failures_unchanged=True,
    live_verification_pending=True,literal_cbat_changes=[],moves=moves,
    roots={str(root):sorted(p.name for p in root.iterdir()) for root in (ROOT,ROOT/'lockscreen',ROOT/'screensaver')})
with audit.open('x',encoding='utf8') as f:json.dump(summary,f,indent=2)
for path in [release,*ROOT.glob('tests/*pipeline*.py'),*ROOT.glob('tests/probe_native_poll_soak.py'),Path(__file__)]:
    compile(path.read_text(encoding='utf8'),str(path),'exec')
print(json.dumps(summary,indent=2))
