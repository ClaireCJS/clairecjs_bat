# PAFPlayer V620 — external enqueue and music library source

- Accept `--q` as an enqueue alias, matching the installed `en.bat`. Disable
  ambiguous workflow-option abbreviation so `--q` cannot become
  `--queue-regex`.
- Queue exact existing local audio files without loading a library filelist.
  Filename hints and regexes continue to resolve on the official player.
- Default the remembered library filelist to
  `C:\mp3\lists\everything.m3u`. The web configuration can save another
  absolute `.m3u`, `.m3u8`, or `.txt` path in existing workflow settings.
- If a filelist is missing, warn for command-line regex searches and search
  indexed tracks, the current queue, and configured music folders. Background
  master-filelist creation remains available when a music root exists.
- Show brief external queue/control activity on the third console HUD detail
  line. The message names the action and source without displaying full paths.
- Allow up to 60 seconds for loopback handoff. A timeout now tells the caller
  that the owner might still finish the request, so they should inspect the
  queue before retrying.
- A verified owner handoff waits up to 15 seconds for the playlist queue bridge
  to become ready during startup before rejecting an enqueue request.
- Report queued-next tracks separately from new playlist entries. Requeuing a
  song already on the playlist does not make a duplicate visible row.

Focused V620 and relevant V615/V616 enqueue tests, syntax checks, and bundle
parity are release gates. An already-running older process requires a restart
to use this code; changing the source does not replace code in its memory.
