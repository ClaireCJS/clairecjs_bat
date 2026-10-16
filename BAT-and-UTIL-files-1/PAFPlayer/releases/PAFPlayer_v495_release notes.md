# PAFPlayer V495 — October 4, 2026

- Ctrl+Break and Ctrl+C now arm a 1.5-second last-resort exit after restoring the terminal and stopping the audio child. This prevents a non-daemon artwork GUI thread from keeping the process alive indefinitely.
- Interrupts between tracks also take the fast-abort path.
- Web queue status requests during startup no longer raise a `current_audio` initialization error.
- No player process was launched or restarted while preparing this release.
