# PAFPlayer V461 — configurable floating-track introduction

- Adds **Next-track title duration** in the web UI's **Floating Lyrics** panel.
- The persisted range is 0–60 seconds in 100 ms increments; the default is 2.5 seconds.
- The setting controls how long Floating Lyrics shows `Artist - Title` at the start of the next track. A real lyric cue replaces it immediately, and 0 disables the held title.
- The setting participates in global-config save/restore along with the other live player settings.

