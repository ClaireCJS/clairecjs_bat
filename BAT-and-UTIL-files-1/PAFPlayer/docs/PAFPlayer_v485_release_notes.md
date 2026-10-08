# PAFPlayer V485 — artwork FPS and responsive bass controls

- Preserves the running instance's artwork, 2×4 detail, palette, bar opacity,
  persistence and visualizer settings. No quality-reduction preset was applied.
- Artwork now uses packed foreground/background/glyph cells and changed-row spans
  instead of silently falling back from semantic-cell transport to full frames.
  NumPy composes exact cells; a bundled 3.5 KiB Windows x64 encoder handles the
  terminal escape encoding. The single Python release contains the encoder;
  no compiler, Numba install or global Python dependency change is required.
  Other platforms or unavailable native loading retain a Python fallback.
- Frame deadlines and governor timings use the high-resolution performance
  counter. Playback, media-monitor clocks and injected test clocks retain their
  original semantics. This fixes coarse 15.6 ms frame timing on Windows Python 3.10.
- Lock-only bass settings no longer restart audio while Windows is unlocked.
  Both direct controls and the lock monitor compare effective bass dB. Audible
  changes use the short interactive preroll. Bass reads no longer scan the
  entire settings registry four times per configuration snapshot or once a second.
- Preserves V484 Ctrl+Break cleanup and V482 console row/wrapping protection.

## Measurements and limits

The running V483 instance was paused before testing. Its actual terminal is
170×47; captured options include processing 63, twin DRCS, detail 9 on both
art layers, seam strategy 5, bar strength 100%, luma blend, opacity 64%,
background strength 30%, and configured visualizer height 32 (31 visible rows
in the isolated fixture's layout). Its observed live sample was 14.03 FPS,
33.06 ms generation EMA, 6.894 ms terminal writes, 30 FPS adapted target.

Final A/B used the captured song's real artwork and decoded spectrum with the
actual show_status renderer and actual Windows Terminal writer. The paused
owner was temporarily suspended; an alternate screen isolated the replay;
its process and display were restored in finally blocks. Each sample lasted
2.5 seconds; audio, popups, web polling and the complete playback loop were
excluded. These are rendering throughput measurements, not monitor-presented
frames or a sustained full-player soak.

| Renderer | Requested FPS | Achieved FPS | Median generation + write |
|---|---:|---:|---:|
| V484 baseline | 120 | 61.34 | 16.28 ms |
| V485 | 60 | 59.92 | 10.06 ms |
| V485 | 90 | 85.19 | 10.44 ms |
| V485 | 120 | 91.89 | 10.55 ms |
| V484 baseline, repeated | 120 | 60.97 | 16.34 ms |

The default target remains 120; actual throughput adapts. 60 FPS is supported
by this renderer test; stable 120 FPS is not established. The already-running
V483 process must be restarted to load V485. Full-player FPS still needs
verification after restart with the usual background workload.

## Validation

22 relevant tests pass: six new tests (30 exact-frame scenarios plus packed
encoder/native-fallback parity and bass-control behavior), 14 existing
renderer/DRCS tests, and two row-guard checks. Two existing web tooltip/layout
assertions also fail in the untouched pre-change baseline; they are recorded
as inherited failures, not silently counted as passes. No full-suite clean
result is claimed. Inactive bass controls were exercised through the actual
nested web-setting handler with registry writes mocked; a live Windows lock
transition was not performed.

See [implementation and operation](../docs/performance-v485.md). Native source
and focused tests are included in the source-and-tests archive. SHA-256 hashes
accompany the release. The previous official V471 installation is preserved;
the beta workspace entry point loads V485 on its next launch.
