# PAFPlayer V656 — command-entry foundation

Adds a nonblocking `#` console command entry shared by the playing and paused
input loops. Enter submits, Backspace edits, Escape cancels, and 1.5 seconds
of inactivity submits. Unrecognized commands display a notice. The existing
Ctrl+Alt+D binding is unchanged.

This is an incomplete step toward the requested AI DJ: `#dj` and `#djforce`
are not implemented, and neither are synthesis, playback coordination, provider
fallback, or settings. No AI network requests are made by this version.

Five focused tests pass; the player and its 27 embedded modules compile and all
27 embedded sources match their editable counterparts. Live console interaction
has not been verified. No literal C:\BAT path was changed.
