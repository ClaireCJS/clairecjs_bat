# PAFPlayer V650 — reduce karaoke-resize stalls

Released November 10, 2026.

After V649, the user reported mostly fluid rendering, with a large remaining
hitch specifically when the three double-height karaoke lines disappear/return
and the visualizer expands/contracts. The V649 transition trace caught roughly
1.5 seconds on the playback thread re-extracting/fingerprinting artwork and
quantizing its cells for a new height. This is distinct from the library lock
and per-poll registry reads fixed in V649.
[Captured transition](../tests/reports/v650-karaoke-transition-V649-20261109-135114.json).

## Changes

- Reuse one track's encoded cover variants across compact, expanded and
  microtile grids. Retention is capped at 32 MiB; oversized sources remain usable
  but are not cached. A different source signature replaces the entry. Source
  extraction is outside the short cache lock, and concurrent extraction keeps
  using the existing single-flight mechanism.
- For the fixed-DRCS seam strategy used in the trace (strategy 5), perform the
  expensive two-color cell quantization with NumPy in 256-cell batches. The
  scalar pair ordering, tie handling, half-to-even rounding, foreground luma and
  downloaded glyph selection are preserved. NumPy absence and other strategies
  retain the existing scalar path. Existing bounded geometry caches retain the
  converted results when returning to a height.

No worker, setting, configuration ID, playback command, font-bank policy, console
encoding or layout behavior was added or changed. Karaoke still disappears in
gaps and the visualizer still fills its rows. The playback owner function is
AST-identical to V649. No audio-processing code changed.

## Evidence and checks

The deterministic cold-cache benchmark uses 140 columns, 42/48 rows and both
background/bar strengths. Scalar conversion took 599–687 ms per layer. The new
path took 89–101 ms after first-use NumPy setup (the first case took 195 ms).
Returning to a cached grid took about 0.003 ms. All four resulting grids matched
the scalar output exactly. These are conversion timings, not end-to-end FPS or
proof that every visible transition is smooth.
[Benchmark](../tests/reports/v650-resize-benchmark-20261110-013413.json).

All **10 new tests pass**, including 156 detail-mode/layout/strength combinations,
uniform colors, distance ties, rounding, sample geometry, fallback, bounded
retention, reuse across four layouts, source replacement and extraction errors.
The **188 existing-test run has 176 passes, 11 failures and one error**, exactly
matching V649. The expanded selection includes artwork/DRCS, seam, transport,
karaoke, popup, diagnostics and workflow tests. Python compilation, 27 bundled
source comparisons and eight generated JavaScript syntax checks pass.

The earlier combined 198-test runs additionally timed out in the existing
five-second silent-playback test. That test passes alone and in V650's clean
188-test comparison; the timeout depends on test ordering. It remains recorded
as a test-isolation limitation, not silently removed or presented as a fully
green suite. One run also emitted Tk's asynchronous-thread cleanup diagnostic.
No new test failed after the zero-brightness edge case was corrected.

- [V650 existing tests](../tests/reports/v650-checks-V650-20261110-013954.json)
- [V649 comparison](../tests/reports/v650-checks-V649-20261110-013750.json)
- [Combined run / focused tests](../tests/reports/v650-checks-V650-20261110-013454.json)
- [Isolated silent-playback pass](../tests/reports/v650-silence-V650-20261110-013706.json)

The test guards blocked attempted writes to live registry/log/history locations.
No literal C:\BAT paths were changed.

### Live V650 follow-up — November 10

The user restarted the official V650 instance with console, artwork popup and
floating lyrics enabled. Two read-only 45-second captures collected 889 thread
snapshots, including a 7.16-second lyric gap, longer than the six-second outgoing
fade. Neither capture sampled the main thread rebuilding artwork. Reported FPS
ranged from 48.4 to 54.43 against a 60 FPS target; the audio-health snapshots
reported zero underruns. The earlier prolonged artwork rebuild did not recur
in these captures.

This is limited sampling evidence, not a frame-by-frame timing measurement.
Diagnostic requests still occasionally took 174–281 ms outside the checked
resize interval. HTTP latency is not frame latency, and the snapshot after a
stall cannot identify everything that delayed it. Sustained playback and the
user's visible-hitch assessment remain unverified. No playback command, setting,
source change or new release was needed for this read-only check.
[Live report](../tests/reports/v650-live-verification-20261110.json).

## Manual verification

Restart the usual player from PAFPlayer.py with console karaoke, artwork popup,
and floating lyrics enabled. Use a song with timed lyrics and gaps longer than
the six-second outgoing lyric fade. Check both the first shrink/expand and later
returns to each height. Confirm the artwork and glyph shapes are unchanged,
lyrics remain synchronized, and audio continues through transitions. Steam's
enabled load reduction still halves the frame target while a game is running.

`tests/probe_v650_karaoke_transitions.py` can collect a read-only 45-second local
trace, retaining cue presence/timing and thread locations without issuing playback
commands or changing settings. Its sampling adds overhead.

Release SHA-256: `f434ec10577fb5e4198cfd5d4c0519018409e8963f383a43b3dd024c2e84cb6e`. The release copy equals tested PAFPlayer.py.
Verified sibling backups were archived; prior releases were preserved.
Project/lockscreen/screensaver roots were audited and need no cleanup move.
play_audio_file.py was not edited. No existing files were deleted.
[Complete affected-path audit](../tests/reports/v650-change-manifest.json).
