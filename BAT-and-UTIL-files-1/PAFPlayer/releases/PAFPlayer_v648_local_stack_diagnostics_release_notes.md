# PAFPlayer V648 — local stall diagnostics

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
& C:\ProgramData\anaconda3\python.exe -B -X utf8 tests\probe_v648_thread_stacks.py
```

The probe verifies the official local player, requests snapshots at no more
than 10 Hz for 20 seconds, and saves JSON in tests/reports. It sends no playback
commands and does not toggle the HUD or change preferences. Sampling itself
adds diagnostic work, and delays while the interpreter is unavailable can hide
some stalls; request durations and GC counters are retained to help interpret
that limitation. The normal endpoint does no stack capture without `stacks=1`.
Do not treat this release as successful freeze repair without examining the
trace and checking live playback afterward.

The new immutable release matches tested PAFPlayer.py: SHA-256 `0f3cfeb92523216db34f27ce36af3e4bbbc10da9dc890c87d2e97833deae1476`.
Required sibling backups were verified and archived. Project/lockscreen/
screensaver roots retain only active files; no cleanup move/deletion was needed.
No literal C:\BAT paths changed. play_audio_file.py was not edited.
See tests/reports/v648-change-manifest.json for the combined affected-path audit.
