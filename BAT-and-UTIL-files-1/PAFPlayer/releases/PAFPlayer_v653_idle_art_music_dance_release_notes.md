# PAFPlayer V653 release notes

Web Config's Experimental section now includes **Dance to music** with the idle
artwork timeout and window-dance range controls. It is off by default and is
saved for later runs.

When enabled, idle artwork consumes `progress_beat_value`, the same
source-timestamp-aligned pulse already used to color and illuminate the console
progress bar. PAFPlayer does not start another analyzer or decode the track a
second time. A quiet or stale pulse produces no movement; stronger pulses scale
the per-frame movement from 1 through 12 pixels. Target clamping prevents
overshoot, while the configured dance range, gallery collision footprints, and
five-pixel monitor guard remain authoritative.

Turning the checkbox off immediately restores the original one-pixel wandering
motion. Changing it in Web Config updates the active artwork window and saves
`ExternalAlbumArtIdleDanceToMusic` in the normal player settings.

Verification:

- `python tests\test_v653_idle_art_music_dance.py -v` — 4 passed.
- V651 idle-dance/session-error tests — 4 passed.
- Existing V86 idle-art tests — 2 passed.
- Python syntax and release-copy parity — passed.
