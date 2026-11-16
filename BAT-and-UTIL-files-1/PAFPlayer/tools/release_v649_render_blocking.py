"""Publish the tested render-blocking fixes, preserving replaced files."""
import hashlib
import json
from prepare_v642_artwork_chrome import ROOT, write

path=ROOT/'PAFPlayer.py'
check=json.loads((ROOT/'tests/reports/v649-checks-V649-20261109-133944.json').read_text())
baseline=json.loads((ROOT/'tests/reports/v648-checks-V648-20261109-073708.json').read_text())
digest=hashlib.sha256(path.read_bytes()).hexdigest()
assert digest==check['source_sha256']
assert check['tests']==162 and not check['errors'] and check['skipped']==0
assert {n for n,t in check['failures']}=={n for n,t in baseline['failures']} and len(check['failures'])==7
release=ROOT/'releases/PAFPlayer_v649_render_blocking.py'
with release.open('xb') as f:f.write(path.read_bytes())
assert release.read_bytes()==path.read_bytes()
notes='PAFPlayer_v649_render_blocking_release_notes.md'
assert not (ROOT/'releases'/notes).exists()
write('releases/'+notes,f'''# PAFPlayer V649 — remove library-lock and input-poll stalls

Released November 9, 2026. Fixes two observed blocking paths; complete freedom
from visualizer freezes is not yet established.

## Evidence and changes

The V648 live trace caught the playback thread and artwork lyric thread waiting
to append diagnostic events while a background library scan held the same lock
across filesystem calls. Eight consecutive samples span about 0.7 seconds.
That trace also includes an intentional learned-tag prompt, so its aggregate FPS
must not be treated as a normal-playback benchmark.

V649 gives the small event history and HUD activity state a separate lock.
Library discovery, index saving, and filesystem access keep their existing lock;
they can no longer hold up these presentation updates. The web log reader copies
event records and their cursor under the new lock. Event history remains bounded
at 1,000 records.

A second V648 trace during normal playback caught the undo observer reading bass
settings from the registry on every empty input poll. V649 establishes an undo
baseline once and observes before real actions and explicit undo. Empty playing
and paused polls do no settings I/O. Individual changes and repeated undo remain
covered; actual bass processing and lock-state detection are unchanged.

No terminal-output encoding, artwork geometry, lyric treatment, playback command,
configuration ID, or stored preference was changed. V647's status-publication
fix and V648's local-only diagnostic endpoint remain available.

## Checks and live verification

162 relevant tests: **155 passed, seven previously documented failures, zero
errors or skips**. Seven new tests exercise real event logging, HUD updates and
web log reads while the library lock is held, concurrent event IDs, empty input
polls, and multi-step undo. Existing workflow tests are included. The seven
failures match V648; this is not a claim that the full historical suite passes.
Python compilation, all 27 bundled-source comparisons, and eight generated web
script syntax checks pass. Test guards blocked attempted registry/log writes
outside the isolated fixtures.
[Test report](../tests/reports/v649-checks-V649-20261109-133944.json).

The user restarted all three lyric displays on V649. A read-only 20-second trace
confirmed the official V649 instance: 199 snapshots, no sampled main-thread undo
registry reads or library-lock waits. This is evidence that the targeted paths
were removed, not proof that a short trace covers all future stalls. Normal V648
and V649 samples both reported roughly 23–27 FPS; these were different playback
moments, not a controlled frame-rate comparison. V649's reported target was
30 FPS. About half of its main-thread samples were inside terminal output, which
remains a material cost. HTTP stack sampling adds overhead and cannot reliably
observe operations that prevent Python from servicing the diagnostic request.

Retained evidence:

- [V648 lock contention](../tests/reports/v648-thread-stacks-20261109-133115.json)
- [V648 normal playback](../tests/reports/v648-thread-stacks-20261109-133255.json)
- [V649 live playback](../tests/reports/v648-thread-stacks-20261109-134537.json)

## Manual follow-up

Keep console karaoke, artwork popup, and floating lyrics enabled. Watch through
several lyric changes and a track transition, including a library refresh. Check
for abrupt console stops while audio continues. Change two settings, then undo
twice and confirm each prior setting is restored. A low average FPS and an abrupt
freeze are separate observations; report both when present. Do not disable the
requested Steam load reduction merely to make the FPS number larger.

Release and active source SHA-256: `{digest}`.
Required sibling backups were verified and archived. Project, lockscreen and
screensaver roots were audited; active inputs remain in place. No literal
C:\\BAT paths changed. play_audio_file.py was not edited. No existing files were
deleted. See [affected paths](../tests/reports/v649-change-manifest.json).
''')
p=ROOT/'docs/README.md';s=p.read_text(encoding='utf-8')
old='Current release: **V648** — local diagnostics for remaining visualizer freezes; retains V647’s status-publication fix.\n[Measurements, limitations, and verification](performance-v519.md#v648-local-stall-capture).'
assert old in s
write(p.relative_to(ROOT),s.replace(old,'Current release: **V649** — separate library scanning from event/HUD updates and remove settings reads from empty input polls.\n[Measurements, limitations, and verification](performance-v519.md#v649-library-lock-and-input-poll-stalls).',1))
p=ROOT/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf-8');head='# PAFPlayer changelog\n\n';assert s.startswith(head)
write(p.relative_to(ROOT),head+'''## V649 — November 9, 2026

Fix two blocking paths found in live V648 stacks: event/HUD publication no longer
waits for the library scan's filesystem lock, and empty input polls no longer
reload bass settings for undo every frame. Preserve event ordering, bounded log
history, individual setting undo, and all render treatments. 155/162 relevant
checks pass with the same seven historical failures and no errors; compilation,
27-module parity and eight web-script syntax checks pass. Live V649 sampling no
longer catches either targeted path; terminal output still consumes substantial
time. Overall freeze resolution remains subject to sustained playback feedback.
[Release notes](../releases/PAFPlayer_v649_render_blocking_release_notes.md).

'''+s[len(head):])
p=ROOT/'docs/performance-v519.md';s=p.read_text(encoding='utf-8')
write(p.relative_to(ROOT),s+'''

## V649 library lock and input-poll stalls

V648's live stack capture found the main playback thread and artwork lyrics
waiting to log while library scanning held the shared lock across filesystem
access. V649 separates small event/HUD state from the library lock. Another
trace caught registry reads from undo observation on empty input polls; V649
observes once initially and before actions/undo instead. The actual bass filter
and lock-detection cadence remain unchanged.

All seven focused regression tests pass, alongside existing workflow and
rendering tests: 155/162 pass with the same seven known historical failures and
no errors. After the user restarted V649, 199 live snapshots no longer caught
either targeted path. Reported FPS remained around 23–27 with a 30 FPS target;
roughly half of the main-thread samples were terminal writes. This is a limited
trace, not proof of sustained freeze-free output or a controlled FPS benchmark.
No console transport/encoding or visual effect was changed in this release.
[Evidence, limitations and manual checks](../releases/PAFPlayer_v649_render_blocking_release_notes.md).
''')
for p in [path,release,*ROOT.glob('tests/*v649*.py'),*ROOT.glob('tools/*v649*.py'),
          ROOT/'src/PAFPlayer_workflows.py',ROOT/'src/PAFPlayer_web_workflows.py']:
    compile(p.read_text(encoding='utf-8'),str(p),'exec')
print(release,digest)
