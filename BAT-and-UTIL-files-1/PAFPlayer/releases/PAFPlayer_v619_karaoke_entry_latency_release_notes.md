# PAFPlayer V619 — Faster console karaoke entry

- Paint the first sung cue before resizing the full-height spectrum in the
  normal console compositing mode.
- Send all double-height lyric rows and vacated-row clears as one synchronized
  terminal payload instead of flushing each row separately.
- Keep visualizer-first ordering for compositing modes that put spectrum or
  artwork in the lyric rows.
- Audio playback remains in the existing audio pump process. Extra render
  processes would contend for the same ordered terminal stream, so this change
  reduces work and terminal writes on the critical path instead.

Terminal presentation time still depends on Windows Terminal, ConPTY, font
rendering, and the selected visualizer detail. A live playback measurement on
the user's console is needed to quantify the remaining transition latency.
