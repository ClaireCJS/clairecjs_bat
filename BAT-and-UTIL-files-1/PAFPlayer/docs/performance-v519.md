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


## V646 karaoke render load

With console, artwork, and floating lyrics enabled, inherited Emojimaxx answer
colors caused repeated Python scans across lyric masks. Colored emoji can leave
an empty region in the monochrome mask; a 900 × 320 region took 332 ms to reject.
V646 performs the search in Pillow's native mask operations, reducing that case
to 0.269 ms and a padded glyph case from 53.17 ms to 1.787 ms. The selected colors
and artwork image hashes remain identical. No quality/cadence setting changed.

New artwork cues still paint immediately. Their old animation timers are
cancelled, and the next color tick waits its usual interval instead of painting
the same fresh layer again at zero delay. Console lyrics retain their existing
refresh limit. No audio, decoder, playback queue, or lyric clock change is part
of this release. Both local and remote tray popup renderers get the shared fix.

The unprofiled synthetic measurements demonstrate reduced helper cost, not a
guaranteed live FPS. Full-size Tk bitmap uploads remain a separate expense
(about 28 ms in the 1920-wide fixture). Live sustained performance with all
three displays and simultaneous gaming remains a manual check after restart.

129 relevant tests were run: 122 passed; seven historical failures reproduce on
V645. Ten new tests include 300 equivalent color cases and animation scheduling.
All 27 bundled sources match, compilation succeeds, and eight web scripts parse.
[Release notes and manual procedure](../releases/PAFPlayer_v646_karaoke_render_load_release_notes.md) and
[comparison evidence](../tests/reports/v646-comparison.json).

From the project directory, run the guarded checks and optional benchmark:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 tests\verify_v646_karaoke_render_load.py
& C:\ProgramData\anaconda3\python.exe -B -X utf8 tests\benchmark_v646_karaoke.py
```

The verifier deliberately returns a failing exit status for the seven retained
historical failures; it does not hide them. Benchmark profiling is off by
default; set `PAF_PROFILE_KARAOKE=1` only to diagnose call costs, not for timings.
Fixtures are retained under `tests/runs`, and reports under `tests/reports`.


## V647 periodic status stalls

The V646 helper optimization did not address long pauses between otherwise
smooth frames. Live timers found periodic web-status preparation taking
133–237 ms/update. Two title fields each triggered a complete reload of 111
persisted settings on the playback/visualizer loop. Those registry calls also
repeatedly yield the interpreter lock, allowing competing rendering work to
amplify the delay. A synthetic busy-Python-thread fixture reproduces this:
the actual expressions took 4.14 ms quiet and 2,229 ms under sustained contention.

V647 uses the two current in-memory title values already maintained by control
and default changes. There are zero bulk settings reads and no polling/cache
delay; the fixture measures about 0.002 ms under contention. Only those two
expressions and release labels differ from V646. Effects and audio are unchanged.

125 of 132 relevant tests pass; seven existing failures match V646. All bundled
sources, Python compilation, and generated web scripts validate. Benchmark
results demonstrate the removed blocking path, not guaranteed FPS. Live V647
status-publication averages fell to 17.56–23.59 ms with all three displays on,
but overall console FPS still varied around 13–23. The remaining freezes are
unresolved; these snapshots are not a controlled FPS comparison. A local stack
capture under the interactive account is prepared in
`tools/capture_v647_visualizer_stacks.ps1`; the agent account lacks memory-read
access to the player. Playback and security settings remain unchanged.
[Evidence, reproducible commands, and manual checks](../releases/PAFPlayer_v647_status_publication_stalls_release_notes.md).


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
the enabled Steam reduction was active for Dungeon Clawler (configured cap:
60 FPS). Roughly half of the main-thread samples were terminal writes. This is a limited
trace, not proof of sustained freeze-free output or a controlled FPS benchmark.
No console transport/encoding or visual effect was changed in this release.
[Evidence, limitations and manual checks](../releases/PAFPlayer_v649_render_blocking_release_notes.md).


## V650 karaoke resize stalls

V649 was reported mostly fluid, with a remaining large hitch when karaoke's six
physical rows are reclaimed or restored. A transition trace caught artwork
extraction/fingerprinting and Python cell quantization on the playback thread.
V650 reuses one source (32 MiB maximum) across geometry changes and batches the
fixed-DRCS seam strategy's quantization in NumPy with exact scalar parity. It
keeps the existing optional-dependency fallback and all other seam strategies.
No worker or audio change was added; the expansion/collapse behavior is retained.

Synthetic cold conversion dropped from 599–687 ms per layer to 89–101 ms after
first-use NumPy setup; the first optimized case took 195 ms. This is not a live
FPS measurement. Ten new tests pass and the 188-test comparison matches V649's
11 old failures and one error. A combined-suite silent-playback timeout passes
in isolation and is retained as a test-order limitation. Compilation, bundle
parity and JavaScript syntax checks pass.

After restart, two 45-second V650 traces collected 889 snapshots with all three
lyric displays enabled, including a 7.16-second gap long enough to finish the
outgoing fade. No main-thread artwork rebuild was sampled. Reported FPS was
48.4–54.43 toward 60 FPS and the audio-health snapshots showed zero underruns.
The previous prolonged rebuild did not recur in these captures. Sampling is not
frame-by-frame timing: occasional HTTP diagnostic delays remained, and the
user's assessment of the visible hitch is still pending.
[Live report](../tests/reports/v650-live-verification-20261110.json).
[Evidence and verification procedure](../releases/PAFPlayer_v650_karaoke_resize_release_notes.md).


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


## V654 native full-frame formatting

The user reported about 95% improvement with V653, with tiny remaining hangs in
ordinary playback. A three-minute live sample ranged from 1.470 to 1.510 GB of
private memory, ending at 1.498 GB, with no audio underruns or popup backlog.
An occasional diagnostic delay remained near GC; this is not frame timing.

V654 removes the per-cell Python color-formatting loop from native packed-artwork
full frames. It reuses the existing encoder and produces exactly the old row
strings, preserving terminal positioning and the dependency/error fallback.
The isolated formatting benchmark improved from 5.50 to 0.66 ms/frame; eight new
tests cover output parity and fallbacks. Existing test failures match baseline.
The slower alternative cache-key experiments were not adopted. Live V654
smoothness and long-session retention remain unverified until restart and use.
[Evidence and procedure](../releases/PAFPlayer_v654_native_full_frame_formatting_release_notes.md).


### V654 live follow-up — November 11, 2026

The official V654 process was verified after restart, with console karaoke,
artwork karaoke and floating lyrics enabled. Two 20-second stack traces and a
three-minute retention sample were collected without changing playback/settings.
The three-minute sample reported 0.0–54.8 FPS, zero audio underruns
and no popup command backlog. Private bytes ranged from
1.338 to 1.434 GB and ended at
1.431 GB; much of the later interval was nearly flat.
This is not a multi-hour stability result.

The first trace crossed a song transition. The second captured a 232 ms HTTP
sampling delay coincident with a generation-2 collection during playback.
Consequently the isolated formatting speedup must not be described as eliminating
all stalls. GC overhead remains a concrete investigation target. HTTP delays are
not direct frame timing; V654's visible smoothness still needs user feedback.
Transport was row-delta in this run, unlike the earlier V653 full-frame sample,
so the FPS numbers are not a controlled before/after comparison.
No runtime code changed during this verification.
[Live results and raw evidence](../tests/reports/v654-live-verification-20261111.json).
