# PAFPlayer V601 release notes

## Rapid global seeking

Ctrl+Alt+Left/Right now preserves each physical five-second tap in order while
another window has focus. Quick reversals remain distinct. Holding the key
starts repeating after 250 ms and continues about every 85 ms. A 5 ms sampler
detects key transitions; exceptionally brief presses between samples may be
missed. Web/console seek bursts retain their existing cumulative behavior.

On the Windows buffered WaveOut renderer, seek handoffs reuse the active Python
audio worker instead of launching another copy of PAFPlayer. A new decoder and
WaveOut output prepare while the old stream keeps playing. Seek output starts
with 1,024-frame blocks and up to 20 ms preroll, then returns to 4,096-frame
blocks for sustained playback. If reuse fails, the
previous replacement-worker path remains available. Other audio modes retain
their existing seek process behavior.

## Verification and limits

Five focused regression tests and six existing live-control tests passed.
A muted live Windows WaveOut test made six consecutive handoffs in 78–94 ms
each, kept the same worker PID, and reported no underruns. Python syntax
parsing passed. A real listening test has not yet been performed. Device and
decoder performance can differ; taps faster than output preparation are
queued and may be heard later rather than instantly.
