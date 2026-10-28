# PAFPlayer V607 — documentation audit

This release corrects documentation and CLI help. Playback, saved settings, integrations, and command routing are unchanged.

- The documentation index now links the current installation, playback, playlist, display, tray, Discord, MonkeyMote, Steam, Last.fm, lock-screen, and screensaver guides.
- The CLI help uses `PAFPlayer.py`, names the playlist input, clarifies that explicit `--default-*` options save defaults, explains Delete's immediate removal and eight-second Yes default, and describes `--readiness-check` and its accepted spelling alias.
- The playlist and Web Config guides state the current 72-hour factory default for **Fresh shuffle after** and its Shuffle by history scope. Earlier V535 behavior remains identified as historical.
- The tray guide describes the current 20-type/10-color chooser. The lock-screen guide points to an existing V520 manual instead of a missing release-note file.
- Local links in the active changelog and versioned manuals were repaired when their targets exist. References to standalone release-note files absent from this checkout were removed or directed to the relevant release history; their substantive feature descriptions remain.

Historical release source copies were not rewritten. Versioned manuals received navigation fixes only. The documentation audit is based on current code and guides; it does not claim a physical Windows playback or shell verification.
