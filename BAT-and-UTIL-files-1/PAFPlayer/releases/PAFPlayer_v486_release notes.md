# PAFPlayer V486 — fused artwork composition and lyric pacing

All source, documentation, snapshots and release packages are saved in the sandbox.
This release has not been deployed to C:\BAT or loaded by the running V485 instance.

## Changes

- Fuse eligible luma artwork composition into the bundled Windows x64 renderer.
  Compute only the half-cell colors needed at bar edges, reuse static cells and
  keep packed semantic transport. No artwork detail or visual settings are reduced.
- Traverse Ghost Frames history once per retained frame, avoiding temporary lists
  and repeated checks for every frequency bin. Other persistence modes are unchanged.
- Cache the floating/artwork text font by size (bounded to 256 fonts), and reuse
  repeated measurements within each floating autosize candidate.
- Cancel an old floating color timer before drawing a new cue. The next decorative
  recolor then waits a full animation interval instead of potentially running
  immediately after the new cue is uploaded.
- Retain V485's responsive inactive lock-only bass controls and precise frame clock.

## Actual-terminal benchmark

Playback was paused. A sandbox worker rendered decoded audio from the captured
instance's song into its actual terminal, with the owner process temporarily
suspended and restored afterward. The fixture used 170×47 layout, processor 63,
Ghost Frames, twin DRCS, both artwork layers, detail 9, luma blending, 64% bar
opacity and 30% background strength. Each segment lasted 2.5 seconds.

| Renderer | Target | Measured callbacks/s | Median work | P95 work |
|---|---:|---:|---:|---:|
| V485 before | 120 | 51.09 | 11.81 ms | 15.09 ms |
| V486 | 60 | 59.72 | 6.85 ms | 8.42 ms |
| V486 | 90 | 89.80 | 6.34 ms | 7.88 ms |
| V486 | 120 | 118.47 | 6.37 ms | 8.14 ms |
| V485 after | 120 | 78.32 | 12.71 ms | 15.50 ms |

This establishes a large reduction in renderer work, not sustained full-player or
physical-display FPS. The baseline's rate variation illustrates scheduling noise.
The suspended owner did not run audio, floating lyrics, capture or web work during
these segments. Live V485 was still approximately 18–36 FPS under its full workload;
V486 full-player FPS and visible cue-transition smoothness need verification when
launched from the sandbox. There is no claim that every lyric hiccup is eliminated.

## Validation

Four V486 tests cover 72 exact ANSI/semantic-frame comparisons with immutable V485,
native-unavailable fallback, 180 persistence frames across resizes/mode switches,
24 exact floating-mask/layout/emoji comparisons, and stale timer cancellation.
Six retained V485 rendering, native fallback and bass-handler tests pass.
The floating-mask timing probe showed modest median improvement; cold font timings
vary and are not a controlled full-GUI performance measurement. The timer test
verifies scheduling behavior without opening GUI windows. No full-suite pass is claimed.

Native source: `tests/PAFPlayer_v486_renderer.c`. Build on MSVC x64 using
`/O2 /Oi /GS- /fp:strict /LD /link /NOENTRY /NODEFAULTLIB /MACHINE:X64`.
The 7.5 KiB DLL is embedded in the single Python source with SHA-256 verification;
no compilation or global dependency changes are needed to run it. Unsupported
platforms, missing NumPy/native loading, and ineligible modes retain prior paths.
The native cache holds at most four static compositions, retaining source identity;
input lengths are checked before native calls.

Evidence: `tests/v486-console-results.json`; reproducible fixtures and tests are
included in the release archive. The captured song must exist to rerun the console
benchmark. Exact rendering and lyric-mask tests do not require that song.
