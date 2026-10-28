# PAFPlayer V577 — remote Save As, FFmpeg setup, and display clarity

Released October 19, 2026.

## Changes

- **Remote tray:** The tray-only right-click menu offers **Save current music
  file…**. A Windows Save As dialog starts with the original filename; a
  progress window and completion/error message report the transfer. The
  official instance checks its identity and logical track visit before and
  during streaming. The tray-only client rechecks both before committing the
  completed file. Existing destination files are never overwritten. Successful
  folders are remembered per remote endpoint in its AppData settings, with
  fallback to the next existing folder and Downloads.
- **FFmpeg:** `--setup-ffmpeg HTTPS-ZIP-URL EXPECTED-SHA256` displays the
  source/destination and waits for `YES` before download. It verifies the full
  SHA-256, rejects unsafe ZIP members, installs in private LocalAppData support
  storage, rescans the installed binaries, and reports version/path. Existing
  PATH tools remain a fallback; PATH itself is untouched.
- **Playlist:** A bounded background worker warms a likely successor's shared
  metadata probe, ReplayGain, edge-silence bounds, and preplay SIXEL cover.
  These cached results avoid repeated preparation at the next handoff.
- **Console:** The Album value can borrow one whitespace cell to line up with
  the same album name in the visible Play path. Emojimaxx no longer substitutes
  `graveyard`, `graveyards`, or `fried`.
- **Web configuration:** The custom frequency spread editor explains display
  width versus source-frequency percentiles, relabels its sliders and profile
  buttons, and adds a live low-frequency explanation. Saved numeric modes and
  named profile data stay compatible.

## Validation and limits

Focused V577 tests cover the HUD, substitutions, frequency UI, remote transfer
and rejection paths, destination history, private FFmpeg setup, ZIP safety, and
successor preparation. Historical tests and Python/JavaScript syntax checks are
recorded in the task report. A live Windows tray Save As and FFmpeg download
were not exercised; both need an interactive machine and, for FFmpeg, a trusted
ZIP/hash pair. The household HTTP connection does not encrypt the audio
transfer; use a trusted network. Partial downloads are recycled; if recycling
fails, the partial file is retained and reported. The playlist worker reduces
startup work but does not yet provide sample-continuous or guaranteed gapless
track transitions. The install survey is reserved for a future prompt.
