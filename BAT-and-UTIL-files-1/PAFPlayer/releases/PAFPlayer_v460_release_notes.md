# PAFPlayer V460 — instant abort and floating-track introductions

- Ctrl+C/Ctrl+Break immediately sends ANSI reset, DEC normal-height (`#5`), homes the cursor, erases to the end of the display, restores autowrap/cursor visibility, and then performs teardown.
- Startup no longer activates the album-art popup or injects a synthetic title-bar click; popup focus changes remain explicit-user actions.
- Floating lyrics withdraw at track end. At the next track start, they briefly show `Artist - Title` for 2.5 seconds, or until a real lyric cue replaces the introduction.
