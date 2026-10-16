# PAFPlayer V521 — responsive audio controls

Released 2026-10-10.

- On the buffered Windows WaveOut backend, volume changes now update gain in the active PCM pump, with no decoder or device restart. Global Ctrl+Alt+Up/Down keeps repeating while held (initial 320 ms hold, then about 85 ms per repeat); normal console key repeat remains available. The already configured 250 ms output reservoir bounds when a gain change reaches the speakers.
- Pause and resume keep the same decoder and queued WaveOut stream. A pause during initial preroll cannot accidentally start the output.
- Console and web seeks now prepare a replacement buffered stream while the current stream continues, start the replacement after a short preroll, then retire the old stream. This removes the stop-first silence, but target decode/startup can still delay the audible jump and the control loop waits for handoff.
- The console visualizer shows “Pause” when pausing and “Unpause” when resuming.
- The FFplay fallback still restarts for volume, pause, and seek. Speed, format, effect, and some other audio changes may still require a restart. This release does not change keyboard mappings.

## Validation

- V521 focused control tests: 6 passed.
- Existing WaveOut worker tests: 5 passed.
- Existing V446 feedback tests: 7 passed.
- Existing V416 player tests: 13 passed using the historical `play_audio_file` import alias.
- Corrected V461 pause feedback test: 1 passed.
- Python source compilation and 7.1/24-bit gain benchmark passed; the gain step averaged about 0.165 ms per 4,096-frame block on this machine.
- A silent real-device WaveOut smoke test passed: live gain, a frozen paused clock, resume, and a held replacement that started only on handoff. Its temporary WAV was sent to the Recycle Bin.
- Audible seek timing and physical held-key latency remain to be verified in a normal Windows playback session. Several unrelated legacy suites have stale fixtures/imports or expectations and are documented in the handoff response.
