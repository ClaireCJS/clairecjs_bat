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
PAFPlayer V745 restores one-second elapsed-time ticks on both the main computer
and tray-only clients. V744 intentionally rounded to five seconds; that regression
is removed. Both endpoints now advance the cached audio timestamp locally before
selecting lyrics, preserving the 250 ms lead, speed, offset, pause, and seek state.
The lock screen can extrapolate a sample for up to 30 seconds instead of sharing
the artwork renderer's four-second cap. The duration bounds the result.

The tray already fetches timestamped cues with the track and caches that timeline.
The local lock-screen bridge reads it without making a request to the master for
each lyric or timer tick. Normal background heartbeats correct transport state;
a detected disconnect or owner change invalidates the bridge immediately.
The 30-second bound limits drift during a delayed heartbeat; it cannot predict
transport actions that have not reached the client. Restart the main player and
reload the tray on THAILOG using the updated single file. The installed signed
V530 companion is unchanged and needs no reinstall. Windows owns the final tile
rendering; visible latency on a locked THAILOG has not been verified here.

Launch the V530 player; installing only the companion cannot add the year/version fields to
an already-running older player. V526 source and formatter regressions are verified;
visible locked-screen layout still needs manual verification after packaging,
installation, and player relaunch.

See the [architecture and manual check](../../docs/windows-lock-screen.md).
Build/install the V530 package with the existing lock-screen tooling. Run
run_regression_checks.py and
test_desktop.ps1 for focused checks. Windows owns actual display timing/layout.
