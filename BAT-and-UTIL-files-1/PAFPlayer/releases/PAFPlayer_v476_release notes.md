# PAFPlayer V476 — direct screensaver bridge launch

`PAFPlayer_screensaver.py` now has a direct-execution entry point. Running the
bridge script no longer exits silently: it locates the compiled
`PAFPlayer.scr` beside it and launches the screensaver in normal mode using the
default PAFPlayer endpoint on port 666.

Arguments supplied to the Python bridge are passed through to the `.scr`, so
preview and configuration modes remain available. If the compiled `.scr` is
missing, the bridge now reports the exact build script needed instead of doing
nothing.

Importing the module from PAFPlayer remains unchanged; the launcher runs only
under `if __name__ == '__main__'`.

Validation: Python compilation passed, and a focused mocked-launch check
confirmed the default `/s /port:666` invocation and executable resolution.

Changed file:

- `../screensaver/PAFPlayer_screensaver.py`
