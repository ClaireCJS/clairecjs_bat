# PAFPlayer V632 — visualizer viewport guard

Released November 1, 2026.

- The console visualizer reserves two unused rows at the bottom of the terminal. This prevents a bottom-row wrap or row advance from scrolling the entire HUD and leaving successive frames in scrollback. The spectrum can be up to two rows shorter.
- Full visualizer frames use an absolute viewport row even in diagnostic modes 14, 16, and 25. Theory 14 remains accepted for command compatibility, but its relative-cursor behavior is retired because other HUD and prompt writes can move the shared cursor.
- The change applies to the same accumulating-frame symptom reported on both V628 and V631; it does not alter audio playback, saved settings, or media files.

Verification: focused visualizer layout, cursor-origin, karaoke reclaim, and row-delta tests; Python syntax and bundled-source parity checks. The supplied pasted transcript does not preserve VT cursor commands, so this is a source-level correction rather than a confirmed live Windows Terminal reproduction. Test it after restarting the player; the already-running process retains its prior renderer.
