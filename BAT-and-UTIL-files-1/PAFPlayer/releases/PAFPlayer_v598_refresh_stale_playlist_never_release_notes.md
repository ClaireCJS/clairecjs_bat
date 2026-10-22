# PAFPlayer V598 release notes

## Accurate Playlist Last play dates

Playlist rows could retain a cached **Never** after a song had just earned a
local playback-history entry. This happened when the browser resolved the row
before the history write and never invalidated that per-path zero value.

V598 marks cached zero values stale after every successful playback-history
write. The Playlist browser sends only those stale values through its existing
background history worker, so the console renderer never waits on SQLite. A
row briefly shows its loading dots, then its actual Last play date.

## Validation

- Python compilation succeeded.
- Focused tests cover stale-Never invalidation after a successful play write and
  the existing recent-shuffle album-alias revalidation behavior.
