# PAFPlayer V591 — live bass transitions

Released October 21, 2026.

Lock/unlock previously stopped FFmpeg and opened a new decoder/output stream to
change the bass shelf. That caused the reported silence despite the correct
V590 lock detection. V591 sends a live gain command to the buffered renderer's
existing named FFmpeg bass filter. The worker, decoder, WaveOut queue and device
clock stay intact. Web bass settings and multiple outputs use the same path.

The low-shelf response, setting IDs, saved values, command-line overrides,
one-second lock polling and official-instance ownership remain unchanged. No new
audio dependency is required. Playback settings were not changed during testing.
Legacy FFplay retains the same-position restart and its possible gap; the live
fix applies to buffered playback. Queued audio still delays audible updates.

## Validation

- 70 focused/relevant checks: **69 passed**, no errors or skips. The one failure,
  `test_seek_restarts_ffplay_at_requested_offsets`, expects three launches but
  receives two; the identical failure is recorded for V589 and V590.
- Eleven new tests cover live lock/unlock, legacy fallback, web changes, private
  stdin ownership, bounded numeric commands, repeated requests, worker routing,
  multiple outputs, unchanged clocks, and actual PCM continuity.
- Actual FFmpeg 4.2.3: 96 kHz, 8 channels, 24-bit; all **672,000 frames / 7 seconds**
  survived 0 → -14 → 0 dB changes, with audio present through both transitions
  and the final marker intact. Low-frequency attenuation measured -14.67 dB at
  40 Hz, with only +0.11 dB at 1 kHz; normal bass returned afterward.
- Real Windows WaveOut, muted: worker PID 74572 stayed unchanged at both gain
  changes, reached all six seconds, and reported **zero underruns**.
- Compilation of the source and 24 embedded modules, plus generated web
  JavaScript, is recorded in the V591 build report.
- No V591 listening/lock/unlock test has yet been performed. Restart your normal
  player to load this version, then follow the
  [manual check](../docs/playback-controls.md#v591-live-bass-transitions).

Reports: [tests](../tests/reports/v591-bass-checks-20261021-104104.json),
[muted native worker](../tests/reports/v591-native-muted-20261021-104335.json),
[initial FFmpeg protocol probe](../tests/reports/v591-ffmpeg-command-probe-20261021-103353.json).

Source SHA-256: `6a10c89e52cbb7d569ea8d2ca13f268cc2d68ae851addba84de82037cec4deec`.

## Files and deployment

The active workspace file and descriptive release copy contain identical Python
source. The versioned manual, changelog and playback documentation were updated.
Required backups were created and hash-verified before every replacement. A
complete path inventory is in `tests/reports/v591-change-manifest.json`.

**No literal C:\BAT paths were changed.** `play_audio_file.py` was not modified.
The running household player was not restarted or sent playback commands. No
settings, UAC, installed package, or Windows lock configuration was changed.
