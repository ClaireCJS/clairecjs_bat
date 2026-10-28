# V519 visualizer output and lock-screen timing

## Bottleneck and change

A read-only sample from the running official V518 player reported 14.05 FPS,
2.453 ms generating each frame and 63.31 ms writing it, with artwork and
semantic-cell transport enabled. The sample did not measure a controlled game
workload. It points to terminal output as the main cost, rather than calculation.

The packed artwork encoder repainted everything between the first and last
changed cell on each row. Two distant changed bars could therefore resend a wide
area of unchanged artwork and thousands of redundant color commands.

V519 compares the exact byte cost of painting each unchanged gap with jumping
over it. It skips gaps when cheaper and only resends color channels that changed.
Each row retains its absolute position and width guards. Every final glyph and
RGB value stays identical. Initial full-frame bytes and native artwork composition
remain unchanged. The native x64 and portable Python encoders are equivalent.
An independent VT interpreter verifies the final cells in regression tests.

The DLL remains embedded and hash-verified, with no runtime download. Its source
is `tests/PAFPlayer_v519_renderer.c`; the build uses MSVC x64 `/O2 /Oi /GS- /LD`
and `/link /NOENTRY /NODEFAULTLIB /MACHINE:X64`, with default precise floating point.
The release also retains the existing portable fallback.

Audio functions, playback priorities, FPS targets, visual settings, artwork quality
and row-alignment guards are unchanged. No frame queue, thread, spin loop or
global timer-resolution change was added. Less terminal work means less avoidable
blocking, without accumulating old frames.

## Measurement

`tests/benchmark_v519_transport.py` compares identical synthetic artwork/bar
frames, 170 columns × 32 rows, with 120 transitions at each input cadence:

| Input cadence | V518 bytes/frame | V519 bytes/frame | Reduction |
| --- | ---: | ---: | ---: |
| 30 Hz | 148,262 | 85,367 | 42.4% |
| 60 Hz | 158,228 | 79,937 | 49.5% |
| 120 Hz | 160,085 | 57,100 | 64.3% |

Median native encoding time fell from about 0.23–0.24 ms to 0.19–0.20 ms.
The benchmark writes no terminal output and plays no audio. These are reductions
in transport work, **not achieved in-game FPS**. Gains depend on changed-cell
patterns and use of the packed artwork semantic-cell path. Other transport modes
keep their established behavior. Game load and terminal presentation can still
limit the visible frame rate.

## Lock-screen lyrics 250 ms earlier

While playing, the V519 compact endpoint selects lyrics at the existing source
position plus the lyric offset plus **0.250 seconds × playback speed**. This gives
a 250 ms lead at the selected speed. Paused/stopped states do not advance. Seeks
use the newly published position, and previous-line context follows the same cue.
Missing timelines retain the existing current-line fallback.

Only lock-screen text receives the lead. Audio position and console, floating,
artwork and browser lyrics are unchanged. Lyrics appear in the top detailed-status
slot; the bottom quick-status badge carries playing/paused/idle/offline only.
The V518 paired badge/text fix remains. Polling stays at 250 ms and player status
updates at 200 ms; Windows can add delay or combine changes, so the lead does not
guarantee exact visible timing or presentation of every very short cue.

Launch the V519 player to load both changes. Updating the companion alone cannot
change a running V518 player's renderer or lyric selection. The publisher still
reads only the verified official instance and never sends playback commands.

## Verification

**164 targeted checks passed:** 67 C#, 84 lock-screen/installer/lifecycle/tray,
and 13 renderer tests. Coverage includes native/fallback agreement, sparse/dense
frames, shape changes, short gaps, buffer bounds, exact 250 ms boundaries, pause,
stop, seek, playback speed, lyric offset and no mutation of other lyric displays.

The complete **678-test embedded suite** ran on V518 and V519: both had 614 passes,
51 failures and 13 errors, with no new failing/error test identities. These existing
failures remain unresolved and are not represented as passing.

An additional old V486 floating-mask fixture was checked separately. Its
`test_masks_and_layout_match_v485` errors on both V518 and V519 because its isolated
namespace omits the newer `_pillow_render_runs` helper. Both reports are retained;
it is excluded from the 164 targeted passes. No floating-mask implementation was
changed for this release.

Python, C# and native compilation, full MakeAppx validation, EXE/MSIX signatures,
pinned installer checks and interactive publication passed. Audio/playback function
bodies and the native luma composition routine match their pre-edit versions.
Prior release hashes were preserved. No literal `C:\BAT` paths, UAC settings or
`play_audio_file.py` content changed.

Reports are directly under `tests/reports`: `v519-comparison-20261010025119.json`,
`v519-renderer-focused-final.txt`, `v519-mask-fixture-baseline.txt`,
`v519-transport-benchmark-20261010024948.json`, and `v519-source-scope.json`.

From the project directory, with previous release sources retained:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 tests\benchmark_v519_transport.py
& C:\ProgramData\anaconda3\python.exe -B -X utf8 tests\run_v519_checks.py
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\run_regression_checks.py
& .\lockscreen\test_desktop.ps1
```

## Manual acceptance

Use the same track, terminal dimensions, artwork settings and game workload before
and after launching V519. Allow transport selection to finish, then compare several
five-second windows using F5 and optionally Ctrl+Alt+F for transport timing. F5
counts callbacks, not monitor refresh. Check artwork/row alignment and uninterrupted
audio. Check a timed-lyric track on the clock/date lock screen, including a gap,
pause/resume and backward seek. In-game FPS and visible lead remain unmeasured.
