# PAFPlayer V649 — remove library-lock and input-poll stalls

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
30 FPS: the Steam monitor detected Dungeon Clawler and the enabled 50% load
reduction halved the configured 60 FPS. That preference was left unchanged.
About half of its main-thread samples were inside terminal output, which
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

Release and active source SHA-256: `8eb44a53975b44a61838bfa68bd23db00c143dc4451024c86d0f8870ad1c0801`.
Required sibling backups were verified and archived. Project, lockscreen and
screensaver roots were audited; active inputs remain in place. No literal
C:\BAT paths changed. play_audio_file.py was not edited. No existing files were
deleted. See [affected paths](../tests/reports/v649-change-manifest.json).
