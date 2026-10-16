# PAFPlayer V535 — playlist resume and shuffle lifetime

Released October 13, 2026.

- A playlist bookmark extremely close to EOF now resumes fifteen seconds before
  the end instead of restarting the song from zero.
- Bookmarks record the following queue entry. If the bookmarked track is removed,
  the next launch continues with that successor; legacy or fully stale bookmarks
  fall back to the first remaining playlist entry.
- Web Config's Playback section now provides a persisted **Fresh shuffle after**
  setting from 0–168 hours. The existing five-hour behavior remains the default,
  while zero requests a fresh history shuffle on every launch.
