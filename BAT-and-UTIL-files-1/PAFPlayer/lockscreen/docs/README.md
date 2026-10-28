# PAFPlayer Lock Screen V530

The single-file player contains the signed companion package, pinned certificate,
installer logic, and Python integration. Run `PAFPlayer.py --install-lockscreen`
to install or update everything. `--check-lockscreen` performs a read-only payload
and registration check. On normal first run, each V530 Windows user gets one
automatic installation attempt; certificate trust still requires explicit consent
through Windows UAC when the certificate is not already trusted. The explicit
command also asks for console confirmation before opening that prompt.

The canonical Python integration module lives at
`src/PAFPlayer_lockscreen.py`. Release builds embed that source in the
single-file `PAFPlayer.py`; it is not a separate deployed runtime dependency.

The detailed-status rows are artist – song, elapsed/total time with the current
lyric, and album with an optional parenthesized year. For example:
`Metallica – One`, `1:15/6:36 · Darkness, Imprisoning Me`, and
`...And Justice for All (1988)`.
The quick-status glyph still indicates playing/paused/idle/offline.

V519's lock-only 250 ms lyric lead and V518's paired badge/text publication remain.
The counter uses actual playback time and changes only at whole seconds. No
independent clock or playback commands are added. Package identity, configuration
IDs and optional enable/disable behavior are preserved.

Launch the V530 player; installing only the companion cannot add the year/version fields to
an already-running older player. V526 source and formatter regressions are verified;
visible locked-screen layout still needs manual verification after packaging,
installation, and player relaunch.

See the [architecture and manual check](../../docs/windows-lock-screen.md).
Build/install the V530 package with the existing lock-screen tooling. Run
run_regression_checks.py and
test_desktop.ps1 for focused checks. Windows owns actual display timing/layout.
