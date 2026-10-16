# PAFPlayer V554 — key order and live playlist progression

- Key-ordered Help lists A–Z and other single keys, including arrows, before
  F1–F10; each base key still keeps its modified bindings on one colored line.
- Playlist view no longer blocks the playback owner indefinitely waiting for a
  key. It checks decoder completion every 25 ms and yields to normal next-track
  selection when the song ends.
