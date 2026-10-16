# PAFPlayer V443 — Half-cell artwork performance and console stability

September 22, 2026. Build `2026-09-22-v443-halfcell-artwork-native-console`.

- Unicode half-cell granularity now uses batched artwork blending and the exact
  precomputed bar-fill boundaries already used by the Twin DRCS renderer.
  Opacity, quantization, feedback brightness, and captured RGB retain their
  previous results. Cropped artwork can also use the batched path.
- Consecutive half cells reuse foreground/background state and send only the
  color components that change. No artwork resolution or color precision is
  removed, and the requested frame rate is not reduced.
- Large writes to a verified Windows console use `WriteConsoleW` directly.
  This bypasses Python 3.10.9's faulty large UTF-8 conversion and avoids the
  scanning, flushing, and separately presented pieces of the 4,096-character
  workaround. Redirects and adapters keep their stream behavior; safe chunks
  remain the fallback when the native writer cannot start. Partial native
  writes continue at the accepted UTF-16 offset without replaying a prefix.
- The fallback parser now recognizes two-byte escape sequences such as ESC 7/8
  without accidentally consuming the next color command.
- V442's scheduled popup states could be partially erased by subsequent spectrum
  frames. V443 caches the popup layout/fade state but includes those cached bytes
  at the end of each changing spectrum frame, before its synchronized-output
  commit. Popup cursor movement also invalidates relative cursor positioning.

Validation: 18 focused V443/V430 tests passed, including visible-cell comparisons
against V442 across blend modes, opacity, feedback brightness, cropping, rounding
boundaries, optional-NumPy fallback, and unchanged Twin DRCS output. Native tests
used a separate hidden Windows console: 30,000- and 120,000-character payloads
read back exactly, with no replacement characters. Partial writes, non-BMP
UTF-16 units, failure after an accepted prefix, and popup commit order were tested.

Moving-artwork benchmark at 200 columns × 32 rows, granularity 2, Signal Aurora,
64% bar opacity: median frame generation fell from 68.46 ms to 9.93 ms (6.9×),
and average UTF-8 payload size fell from 213,980 to 99,135 bytes (54% less).
Run `python -B -X utf8 test_play_audio_file_v443.py --benchmark` to reproduce.
These are offline generation/payload measurements, not a live FPS claim.

The running V442 session was left playing and reported zero audio underruns.
Restart PAFPlayer with V443 to load these changes; live Windows Terminal FPS
and the user's specific remaining twinkling need verification after restart.
