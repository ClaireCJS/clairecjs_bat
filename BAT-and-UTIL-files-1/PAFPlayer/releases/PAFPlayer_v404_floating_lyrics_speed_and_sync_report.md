# PAFPlayer V404 floating lyrics speed and sync

The floating lyric renderer no longer uses Pillow's square `MaxFilter` for the
large outline on every cue. `expand_lyric_outline` uses an exact separable NumPy
maximum operation, with Pillow retained as the fallback. A randomized
differential check covered 35 image sizes and filter radii against Pillow's
original output.

The artwork popup and floating window now receive the same current karaoke cue.
The artwork-only early cue lead was removed. Lyric commands use a latest-value
mailbox, so a slow paint cannot build a stale queue of old lines. Both surfaces
are prepared in the same Tk callback, and pending resize paints are cancelled
when a cue arrives.

Console lyrics remain on the existing 5 Hz schedule. A cue transition may cause
one immediate repaint so a boundary is not held for the next periodic tick;
there is no high-rate console lyric animation loop.

The browser status now carries the shared lyric timeline and karaoke offset.
The browser preloads the next few styled cues and switches by the shared
playback clock instead of waiting for a separate style request after each
status poll.

Measured renderer timings for a 1920x700 floating lyric:

- first layout: 78.03 ms (7.30 ms after Pillow imports were warm)
- first color render: 27.92 ms
- cached recolor: 18.62 ms
- previous MaxFilter shadow step: about 644 ms

Validation:

- `test_play_audio_file_v402_audio_ui.py`: 12 tests passed
- `test_play_audio_file_v401_bar_art.py`: 7 tests passed
- embedded V404/sync, shadow, queue, and animation tests: 7 tests passed
- AST parse and exact shadow differential checks passed

