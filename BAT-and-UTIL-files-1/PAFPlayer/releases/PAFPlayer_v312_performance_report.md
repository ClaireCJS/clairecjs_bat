# PAFPlayer V312 performance and curation report

## Executive summary

V312 starts from the exact V311 sandbox source (SHA-256
`C3BD96FDD8BB2E0BC762D1FD4C2D28194808A5EEEE4BA176D95F6607EB19D612`).
It keeps console FPS, visual detail, terminal resolution, audio quality, and web
behavior unchanged. The largest measured result is the tall no-art console
visualizer: 35-row generation is 79–82% faster, and the 48-row semantic path is
83% faster. Live-input FFT conversion is 64% faster. Four concurrent artwork
consumers complete 85% sooner because identical extraction is performed once.

The quality change removes 121 overreaching Emojimaxx verb-form substitutions.
Every removed word and its V311 glyph has a stable `EMX312-###` undo code in
`play_audio_file_v312_emojimaxx_removals.md` and in the source manifest.

## Provenance and method

- Input: `play_audio_file_v311_art_move_freeze_learned_glyph.py`, V311.
- Pre-edit backup: `play_audio_file.py.bak.202608271429.replaced-by-chatgpt.bak`.
- The archive and backup are byte-for-byte identical: 2,861,090 bytes and the
  SHA-256 above.
- Profiling used deterministic synthetic spectrum frames, representative 160
  terminal columns / 320 Twin-DRCS logical columns, 16/35/48 rows, artwork-on-
  bars plus artwork-on-blackness, live 16-bit PCM, and a real two-art track.
- Timings are Python generation/worker wall time; terminal emulator paint time
  is intentionally not inferred from CPU generation benchmarks.
- Specialist workstreams audited rendering/terminal output, audio/concurrency,
  web/art/history, and general hot paths read-only. The primary pass accepted
  only findings supported by profiles or exact duplicate-work evidence.

## Architecture reviewed

- Owner playback/UI loop and FFplay/native-output process lifecycle.
- Paced FFmpeg spectrum worker, cached timelines, live loopback/microphone FFT.
- Console DRCS renderer, semantic-cell/row-delta transport, terminal writes.
- Web HTTP/status/spectrum transport and demand gating.
- Artwork extraction, external-art GUI, web art, console-art grids.
- SQLite playback history, shuffle scoring, metadata and Last.fm workers.

## Baseline bottlenecks

The 35-row no-art cProfile recorded 7.21 million calls over 30 frames. Of 2.137
seconds total instrumented time, `colored_cell()` consumed 1.409 seconds across
326,400 calls. Per-cell RGB quantization alone created 688,368 generator calls;
`max`, `min`, and `round` accounted for another large fraction. The root cause
was a `source_rows < 24` gate that disabled the already-correct Twin-DRCS fast
path for tall layouts.

Artwork extraction was independently launched by the web UI, external artwork
window, and artwork-existence probe. Four same-track callers repeated reads,
SHA-256 hashes, Pillow decoding, and visual fingerprints.

Live PCM conversion rebuilt the same Hann window, FFT frequency array,
logarithmic edges, and 640 search boundaries for every 320-column callback.
Baseline median was 2.379 ms per callback.

Short tracks at or below the 60-second silence-scan window launched two
byte-identical FFmpeg scans. Early track navigation also left the paced spectrum
daemon alive indefinitely at its frozen-playhead wait gate.

## Implemented changes

1. Enabled the no-art row-independent Twin-DRCS fast path at all visualizer
   heights. Tall RGB quantization is computed once per logical column, in the
   same order as V311, before left/right blending.
2. Removed unused per-cell energy clamping for row-independent processors and
   replaced measured fixed-three-channel generator tuples with exact RGB tuples.
3. Added a transient artwork single-flight. Concurrent consumers share one
   result; there is deliberately no persistent variants cache, stale-art window,
   or long-playlist byte retention.
4. Cached only immutable live-FFT geometry in a bounded 32-entry LRU. PCM,
   magnitudes, maxima, dB math, rounding, and output bytes are not cached.
5. Reused the leading silence intervals when the trailing scan is provably the
   identical `(start=0, span=duration)` request.
6. Signals the track-local analyzer stop event on every cleanup path. Cleanup
   does not block on a join while an FFmpeg chunk winds down.
7. Removed 121 ordinary verb/verb-form Emojimaxx mappings with individual undo
   codes; literal nouns and object mappings remain.

## Before/after benchmarks

| Workload | V311 average | V312 average | V311 p95 / p99 | V312 p95 / p99 | Change |
|---|---:|---:|---:|---:|---:|
| 35 rows, no art, full ANSI | 35.090 ms | 7.274 ms | 47.330 / 56.758 ms | 7.700 / 12.745 ms | 79.3% faster |
| 35 rows, no art, semantic cells | 32.484 ms | 5.794 ms | 34.162 / 38.176 ms | 5.848 / 5.862 ms | 82.2% faster |
| 35 rows, art on bars + black | 47.257 ms | 38.244 ms | 53.238 / 61.459 ms | 39.628 / 41.325 ms | 19.1% faster |
| 48 rows, no art, semantic cells | 44.020 ms | 7.607 ms | 49.776 / 57.503 ms | 7.754 / 9.498 ms | 82.7% faster |
| Live PCM FFT, 1024 samples, 320 columns | 2.431 ms | 0.868 ms | 2.474 / 3.520 ms | 0.887 / 1.188 ms | 64.3% faster |
| Four concurrent artwork consumers | 277.9 ms wall | 43.2 ms wall | — | — | 84.5% faster |

The existing 16-row no-art path did not regress: repeated median measurements
were 3.192 ms in V311 and 3.165 ms in V312. The short-track silence check now
uses one FFmpeg invocation instead of two and returned identical `(0.92, 9.08)`
bounds in the controlled test. Long tracks still use two distinct edge windows.

## Verification

- `python -m py_compile play_audio_file.py`: pass.
- `--version`: reports V312 and the V312 build identity.
- 174 randomized V311/V312 renderer comparisons (24/35/48 rows plus artwork):
  byte-identical ANSI output.
- 375 cold/warm V311/V312 live-FFT cases plus 32 concurrent calls:
  byte-identical result bytes; cached Hann arrays are read-only.
- Eight simultaneous artwork callers: one underlying extraction, eight equal
  fresh lists. A later call re-extracts; no stale persistent cache. The failure
  path wakes all waiters and clears in-flight state.
- Real-art comparison: V311/V312 variant SHA-256 lists identical.
- Edge-silence comparison: identical short/long bounds; short call count 2→1,
  long call count remains 2.
- Six focused embedded renderer/live-spectrum/art tests: all pass.
- Full legacy suite, quiet V311/V312 A/B: 557 tests each. Both have exactly the
  same 34 failure IDs and 14 error IDs under this environment; V312 added zero
  failure/error/skip IDs. Those inherited failures cover stale historical UI
  contracts and filesystem/SQLite environment assumptions, not V312 changes.

## Rejected or deferred changes

- Emojimaxx replacement itself averages about 0.15 ms uncached and is cached in
  normal display use. Regex restructuring was rejected as irrelevant to the
  measured bottleneck; V312 changes its curation, not its engine.
- Web publish/snapshot/JSON measured about 0.215 ms average and is already
  demand-gated. No web update-rate or visual-quality reduction was made.
- History normalization is roughly 0.005 ms; 10k-track shuffle work is slower
  but already progressive/background. Database restructuring was deferred.
- An asynchronous terminal writer risks stale/reordered UI frames and was not
  justified by the generation profile.
- One persistent backpressured FFmpeg analyzer could avoid repeated 3-second
  process launches, but it is architectural work requiring seek, clock, and
  cancellation tests. It was not smuggled into this safe pass.
- Vectorized FFT bin maxima and artwork geometry fast paths were deferred because
  their boundary/rounding semantics need separate differential campaigns.

## Remaining opportunities

1. Replace repeated 3-second spectrum subprocesses with one cancellable,
   backpressured analyzer process; measured cumulative short-chunk overhead is
   about three times a continuous analysis.
2. Bound the older primary raw-art byte caches after measuring RSS across large
   playlists; do not conflate that with the safe transient single-flight.
3. Avoid repeated native output-meter loops in multi-output mode and eventually
   share one decode pipeline across endpoints, with clock/backpressure tests.
4. Give audio-health and other per-track background workers cancellation tokens
   so rapid skips cannot accumulate low-priority work.
5. Model native WaveOut preroll in the audible playback clock before changing
   karaoke/history timing.

## Confidence and limits

Confidence is high for result equivalence in the modified pure-Python paths due
to direct V311/V312 byte comparisons. The visualizer benchmarks isolate renderer
generation; real terminal FPS also depends on Windows Terminal/ConPTY paint and
the active palette/artwork mode. No FPS cap, row reduction, palette reduction,
audio-quality reduction, or web-priority increase was used to obtain these wins.
