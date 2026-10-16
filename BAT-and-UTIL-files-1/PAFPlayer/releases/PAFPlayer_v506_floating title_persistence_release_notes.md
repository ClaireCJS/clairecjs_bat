# PAFPlayer V506 — Floating Lyrics title duration

- When no duration has been saved, `Display song title for first` defaults to 25 seconds.
- On startup, PAFPlayer applies the saved `FloatingLyricsTrackIntroSeconds` value to the live Floating Lyrics timer. Previously it loaded that value but left the timer at the built-in default.
- Track transitions include the live duration in the normal settings snapshot, so a web change remains consistent through playback and restart.
- Existing fractional-second values and the read-only `FloatingLyricsTrackIntroMs` migration fallback remain supported. The web control still accepts 0–60 seconds in 0.01-second steps.

Validation: focused V476, V501, and V506 title-duration regression tests; Python compilation and broader relevant tests are recorded with the release handoff.
