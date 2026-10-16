# PAFPlayer V479 — Floating Lyrics center-button chrome fix

Fixed a Floating Lyrics issue where pressing **Bring to Center** or **Center
Over Visualizer** could leave a flashing visible border around the lyrics until
the window was clicked and focus was moved away.

Button-driven repositioning is now tracked separately from mouse movement. The
window temporarily enters its editable state to perform the move, then returns
to the normal transparent/borderless lyric state immediately afterward. Mouse
dragging and intentional edit/focus interactions retain their existing chrome.

Validation: Python compilation and focused source checks passed for the
button-move state, deferred border restoration, and focus-event guard.

Changed files:

- `../PAFPlayer.py`
- `../docs/floating-lyrics.md`
