"""Publish the tested bounded diagnostic; preserve every replaced file."""
import hashlib
import json
from prepare_v642_artwork_chrome import ROOT, write

path=ROOT/'PAFPlayer.py'
check=json.loads((ROOT/'tests/reports/v648-checks-V648-20261109-073708.json').read_text())
baseline=json.loads((ROOT/'tests/reports/v647-checks-V647-20261109-072329.json').read_text())
digest=hashlib.sha256(path.read_bytes()).hexdigest()
assert digest==check['source_sha256']
assert check['tests']==138 and not check['errors'] and check['skipped']==0
assert {n for n,t in check['failures']}=={n for n,t in baseline['failures']} and len(check['failures'])==7
release=ROOT/'releases/PAFPlayer_v648_local_stack_diagnostics.py'
with release.open('xb') as f:f.write(path.read_bytes())
assert release.read_bytes()==path.read_bytes()
notes='PAFPlayer_v648_local_stack_diagnostics_release_notes.md'
assert not (ROOT/'releases'/notes).exists()
write('releases/'+notes,f'''# PAFPlayer V648 — local stall diagnostics

Released November 9, 2026. **Diagnostic release; remaining freezes are not fixed.**

V647 removed the two bulk settings reloads from periodic status publication.
Live publication time improved to roughly 18–24 ms, but console rendering still
stalled. External py-spy capture was blocked under the agent account and failed
with Windows error 299 under the interactive account; no usable stack trace was
obtained. No security/UAC setting was changed to work around either failure.

V648 adds an opt-in location snapshot to the existing endpoint:
`GET /api/runtime-diagnostics?stacks=1`. Stack requests are accepted only from
the player computer. Ordinary diagnostics retain their existing behavior.
Each requested snapshot contains at most 64 threads and 32 frames per thread,
with the main thread first. Only thread name, source basename, function name,
and line number are returned. No local variables, source contents, or retained
frame objects are included. There is no sampler/background thread and no new
work on the playback/render loop when nobody requests a snapshot.

The V647 status fix, V646 color-scan fix, all rendering effects and current
configuration IDs are preserved. Audio/playback controls are unchanged.

## Checks

138 relevant tests: **131 passed, seven historical failures, zero errors/skips**.
The failures match V647. Six new tests cover a real waiting worker, main-thread
priority, thread/depth bounds, reference cleanup, absence of locals, inactive
default behavior, and local/remote HTTP access. Compilation, 27 bundled-module
comparisons, and eight generated web-script syntax checks pass. This is not a
claim that the complete historical suite passes.
[Test report](../tests/reports/v648-checks-V648-20261109-073708.json).

## Capture the remaining freezes

Restart the usual PAFPlayer from the updated workspace with console, artwork,
and floating lyrics enabled. The agent can then run:

```powershell
& C:\\ProgramData\\anaconda3\\python.exe -B -X utf8 tests\\probe_v648_thread_stacks.py
```

The probe verifies the official local player, requests snapshots at no more
than 10 Hz for 20 seconds, and saves JSON in tests/reports. It sends no playback
commands and does not toggle the HUD or change preferences. Sampling itself
adds diagnostic work, and delays while the interpreter is unavailable can hide
some stalls; request durations and GC counters are retained to help interpret
that limitation. The normal endpoint does no stack capture without `stacks=1`.
Do not treat this release as successful freeze repair without examining the
trace and checking live playback afterward.

The new immutable release matches tested PAFPlayer.py: SHA-256 `{digest}`.
Required sibling backups were verified and archived. Project/lockscreen/
screensaver roots retain only active files; no cleanup move/deletion was needed.
No literal C:\\BAT paths changed. play_audio_file.py was not edited.
See tests/reports/v648-change-manifest.json for the combined affected-path audit.
''')
p=ROOT/'docs/README.md';s=p.read_text(encoding='utf-8')
old='Current release: **V647** — remove bulk settings reloads that stall periodic visualizer updates.\n[Measurements, limitations, and verification](performance-v519.md#v647-periodic-status-stalls).'
assert old in s
write(p.relative_to(ROOT),s.replace(old,'Current release: **V648** — local diagnostics for remaining visualizer freezes; retains V647’s status-publication fix.\n[Measurements, limitations, and verification](performance-v519.md#v648-local-stall-capture).',1))
p=ROOT/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf-8');head='# PAFPlayer changelog\n\n';assert s.startswith(head)
write(p.relative_to(ROOT),head+'''## V648 — November 9, 2026

Add bounded, on-demand, local-only thread locations to runtime diagnostics after
external profiling failed. No local variables, source contents, frame retention,
background sampler, or render-loop work. Preserve the V647 status fix. Remaining
visualizer freezes are still under investigation. 131/138 relevant checks pass;
the same seven historical failures remain, with no errors, plus compilation,
27-module parity, and eight web-script syntax checks.
[Release notes](../releases/PAFPlayer_v648_local_stack_diagnostics_release_notes.md).

'''+s[len(head):])
p=ROOT/'docs/performance-v519.md';s=p.read_text(encoding='utf-8')
write(p.relative_to(ROOT),s+'''

## V648 local stall capture

External profiling failed (agent account: access denied; interactive account:
Windows error 299), so V648 adds optional `stacks=1` to runtime diagnostics.
Only local clients can request thread locations. Results are capped at 64
threads × 32 frames and exclude locals/source contents; captured frame references
are cleared before returning. Default diagnostics do not sample stacks, and no
background or frame-loop work is added. This is diagnostic support, not a claim
that the remaining freezes are fixed. It retains V647's measured status fix.

After restarting the usual player, `tests/probe_v648_thread_stacks.py` can capture
20 seconds at up to 10 Hz without issuing playback commands. Reports are saved
under tests/reports. Sampling has overhead and cannot observe Python executing
while another operation prevents the interpreter from servicing HTTP; use the
recorded request delays and GC counters alongside the stack locations.
[Details and checks](../releases/PAFPlayer_v648_local_stack_diagnostics_release_notes.md).
''')
for p in [path,release,*ROOT.glob('tests/*v648*.py'),*ROOT.glob('tools/*v648*.py')]:
    compile(p.read_text(encoding='utf-8'),str(p),'exec')
print(release,digest)
