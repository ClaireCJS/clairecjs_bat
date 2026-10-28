# PAFPlayer V627 — queueing guide and truthful resume labels

Released October 27, 2026.

- The startup resume notice now prints the playlist's filename and the song's filename on separate lines. The filename columns align, both filenames use ANSI italics where the terminal supports them, and the song line keeps the saved playback time.
- `docs/music-library-and-enqueue.md` now has one section collecting command-line `-q`/`-qa`/`-qe`, `en.bat`, regex search, console playlist and library selectors, web queue controls and drops, native artwork/floating-lyrics/tray drops, and remote tray/API routes. It distinguishes the saved enqueue-placement preference from commands that explicitly queue next, and explains that a live queue edit does not automatically save a playlist file.
- No queue placement or playback behavior changed in this version.

Verification: focused resume-format tests, existing resume/enqueue/queue tests, Python compilation, and byte-for-byte active/release parity. ANSI italics depend on terminal support.
