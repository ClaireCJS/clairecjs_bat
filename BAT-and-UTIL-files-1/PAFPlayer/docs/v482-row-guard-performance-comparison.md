# V482 row-guard performance comparison — 2026-10-01

## Scope and conclusion

Diagnostic only: no player implementation or preferences changed. Running
V483 was paused for isolated benchmarks, then resumed for a short live profile.
Current workspace source was V484. Both retain the V482 row guard.

The results do not support the added no-wrap prefix being the primary cause
of the reported 60-to-13 FPS regression. They do not rule out a Windows
Terminal-specific interaction. No end-to-end old/new Windows Terminal test
was performed, and no performance fix is claimed.

## Isolated A/B

`tests/benchmark_v482_row_guard.py` uses the existing renderer-only harness,
real Dethklok TV-edit metadata/lyrics, synthetic spectrum, 170-by-45 geometry,
and 240 frames spanning playback seconds 25–33. It starts no audio/workers and
suppresses history/settings writes. Only the row prefix changes. This is not
the running player's complete artwork/audio/background workload.

Pre-V482 prefix: charset reset + absolute cursor address + optional DEC #5.
V482 adds CSI ?7l (disable wrapping) before that prefix. Verified against
the V481 source backup. New payloads contain 47,350 extra characters across
240 frames, approximately 197 characters/frame (0.64% of captured output).

First generation run, old/new/new/old, mean milliseconds per frame after
20 warm-up frames: **15.646 / 15.955 / 16.173 / 15.816**. This preliminary
old-path implementation stripped the prefix from the new helper.

Repeat using the actual old prefix construction: **15.728 / 17.542 /
21.209 / 20.701**. The late old trial slowed too, demonstrating significant
system-load/time drift; these are not controlled statistical confidence bounds.

Native replay used identical captured payloads, removing only the new
row-prefix guard for the old case, through the real console writer in a
separate hidden Windows legacy console. It is NOT Windows Terminal.

First 8-block old/new/new/old sequence repeated, 240 frames/block:

| Path | Per-block write ms/frame |
|---|---|
| Old | 13.677, 19.451, 20.021, 19.126 |
| Guarded | 14.212, 21.803, 18.373, 17.482 |

A shorter repeat (24 frames/block) measured:

| Path | Per-block write ms/frame |
|---|---|
| Old | 18.099, 18.032, 18.322, 18.185 |
| Guarded | 18.404, 17.875, 18.632, 24.072 |

There is noise and an outlier, but no consistent several-fold guard penalty.
Replay timing measures synchronous writes, not actual display presentation FPS.

## Live V483 profile

Song at baseline: My Life With The Thrill Kill Kult — Dope Freek.
Transport: semantic-cell; background artwork enabled; target had adapted to
30 FPS. Baseline measured approximately 15 FPS before pausing.

With the built-in runtime-only profiler enabled, three five-second windows:

| Metric | Window 1 | Window 2 | Window 3 |
|---|---:|---:|---:|
| Actual FPS | 12.88 | 12.48 | 9.31 |
| Render-call average ms | 30.553 | 34.535 | 36.415 |
| Terminal-write average ms | 5.791 | 10.579 | 9.581 |
| Player CPU percent | 154.7 | 132.5 | 145.5 |

The render component surrounds `render_drcs_visualizer` and argument
preparation, before output transport/row positioning. It alone exceeds the
16.7 ms total budget for 60 FPS. These component averages have different call
counts and must not simply be added to derive total frame duration. The
profiler also adds overhead; its FPS is not an uninstrumented benchmark.

Next investigation: profile inside visualizer generation (including artwork
composition) under the actual active settings, then compare any candidate
optimization against the same captured inputs. Retain the scrolling guard
until a controlled test identifies a reason to change it.
