# V486 renderer performance and lyric transitions

V486 preserves the existing 120 FPS request and adaptive governor. Its fused luma
composer accelerates the current static artwork/twin-DRCS configuration without
changing image detail, palette, opacity, Ghost Frames or output bytes. Typical
actual-terminal benchmark work fell from about 12 ms to 6.4 ms; a short isolated
run reached 118.5 callbacks/s. Full-player throughput remains unverified.

The native composer uses exact rounding and validates buffer lengths. Unsupported
configurations retain the V485 NumPy/scalar renderer; native failure does not remove
rendering support. Static composition caching is bounded to four entries.

Floating cue changes reuse loaded text fonts and duplicate autosize measurements.
A new cue cancels the prior animation deadline before rendering, then schedules the
next color frame after a full interval. This avoids immediately recoloring the same
fresh cue. Mask pixels, wrapping, emoji and placement match V485 in regression tests.
These changes reduce transition work; a real full-player lyric-stutter fix is not
claimed solely from isolated tests.

See [release history](PAFPlayer_changelog.md),
[floating lyrics](floating-lyrics.md), and [retained V485 behavior](performance-v485.md).
All files remain in the sandbox; restarting an older installed copy will not load V486.
