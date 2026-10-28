# PAFPlayer V590 — working locked-session bass reduction

Released October 20, 2026.

The running V586 player had Bass Reduction while Locked enabled at 70%, but its
input-desktop probe could miss a locked Windows 10 session. The user's real
lock/unlock trace captured 49 locked samples: 8 returned Windows access denied
while the old ctypes error remained 0, and 41 still exposed an input desktop.
Windows session information correctly reported locked throughout and unlocked
on return.

V590 uses the documented session flag via WTSQuerySessionInformationW, with
private, correctly typed bindings and captured errors. It never calls
SwitchDesktop. A read-only desktop query remains a best-effort fallback if
session information is unavailable. Native bindings/types are cached once,
and every returned session buffer and opened desktop handle is released.

A second bug stopped the decoder with `continue` inside its polling loop. That
could enter the natural-EOF branch and finish the track. The bass monitor now
breaks out to reconstruct the same track at its current position, applying or
removing the existing low-shelf filter. This still uses a short decoder restart;
a completely inaudible transition is not claimed.

Setting IDs, saved preferences, percentage mapping, CLI overrides, and the
one-second polling interval are unchanged. Web `/api/status` adds the last
observed `session_locked` and `bass_effective_db` values; these begin as null.
No UAC, installation, playback-command routing, or literal C:\BAT change was made.

## Verification

- 46 of 47 focused and related checks passed, including all 12 new lock API,
  error-handling, pointer-width, memory-lifetime, restart and decoded-audio checks.
- The remaining seek test expects three decoder commands and gets two on both
  untouched V589 and V590. It is retained and reported as an existing failure.
- The new same-song transition regression fails on untouched V589 by entering
  natural EOF, and passes on V590 for both lock and unlock.
- Actual FFmpeg-decoded test audio at the user's 70% reduction measured
  **-14.67 dB at 40 Hz** and **+0.11 dB at 1 kHz**. Unlocking produced samples
  identical to the initial unlocked output. This test wrote only isolated
  fixtures and rendered into a pipe, without playing test tones aloud.
- The user performed a real lock/unlock cycle: the repaired detector followed
  both transitions. A subsequent 500-query native run took about 0.25 seconds;
  handles stayed 128 → 128 and ctypes pointer types stayed 21 → 21.
- Six Python files and all 24 bundled modules compiled; all eight generated
  web JavaScript blocks passed syntax checks. The immutable release source is
  hash-identical to the tested main source.

Reports:

- [Focused checks](../tests/reports/v590-bass-checks-20261020-212649.json)
- [Untouched V589 comparison](../tests/reports/v589-bass-baseline-checks-20261020-212349.json)
- [Native lock trace](../tests/reports/v590-native-lock-20261020-211846.jsonl)
- [Native resource checks](../tests/reports/v590-native-cache-20261020-212733.json)
- [Compilation and JavaScript](../tests/reports/v590-build-20261020-212658.json)
- [Affected paths and backups](../tests/reports/v590-change-manifest.json)

## Final listening check

Restart using the workspace PAFPlayer.py (V590), play a bass-heavy track, then
lock Windows for at least five seconds and unlock. The bass should reduce while
locked, return on unlock, and stay on the same song. The live detector and actual
decoded filter were verified separately; listening through the household
player after restart remains unverified. See the
[bass controls guide](../docs/playback-controls.md#v590-lock-detection-and-restart-repair).

Windows' documented
[session flags](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/ns-wtsapi32-wtsinfoex_level1_w)
distinguish locked/unlocked sessions. Python's
[ctypes error-capture documentation](https://docs.python.org/3.13/library/ctypes.html)
explains why the old `windll` call did not update `get_last_error()`.
