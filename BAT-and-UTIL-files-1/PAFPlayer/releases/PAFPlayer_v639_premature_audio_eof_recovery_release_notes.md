# PAFPlayer V639 — Premature audio end recovery

November 2, 2026

- Detects a decoder exit more than five seconds before the known track end by
  checking the WaveOut playback clock rather than assuming exit code zero means
  the whole song played.
- Resumes the missing tail with at most two retries. When a RAM loopback source
  stops early and the source file still exists, recovery reads from that file.
  This can briefly restore a file lock and cause a short audio handoff gap.
- A failed recovery raises a runtime warning and does not claim a complete
  play. Normal playback, manual track changes, and short end padding keep their
  existing behavior.
- The reported `04_Magic Johnson.mp3` regression runs muted in an isolated
  WaveOut worker. It skips with a warning if that file or the needed audio
  output is unavailable; it never addresses the official player.
