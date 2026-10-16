# PAFPlayer V475 — preserve console output during shutdown

Terminal cleanup no longer clears the existing PAFPlayer console screen.
Normal exits, Ctrl+C, cleanup handlers, and `atexit` restoration preserve the
player’s output and scrollback while restoring cursor visibility, autowrap,
colors, and terminal mode.

An intentional Ctrl-Break shutdown is the only special case: it moves the
cursor down to the bottom of the console and emits one additional newline so
the next prompt begins after the existing output. It still never erases the
screen or emits a clear-screen sequence.

Validation: Python compilation and focused source checks passed. The focused
checks verify that terminal restoration contains no erase-display sequence,
supports the explicit Ctrl-Break path, and keeps the normal cleanup path
screen-preserving.

Changed file:

- `../PAFPlayer.py`
