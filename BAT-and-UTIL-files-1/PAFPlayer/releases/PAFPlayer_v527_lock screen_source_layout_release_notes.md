# PAFPlayer V527 release notes

Released October 12, 2026.

The canonical development source for the Python lock-screen integration moved to
`PAFPlayer/lockscreen/src/PAFPlayer_lockscreen.py`. The installer, diagnostics,
bundle synchronization utility, and tests now resolve that location.

The module remains embedded in the single-file `PAFPlayer.py` and versioned
release, so deployed playback still has no separate Python-module dependency.
