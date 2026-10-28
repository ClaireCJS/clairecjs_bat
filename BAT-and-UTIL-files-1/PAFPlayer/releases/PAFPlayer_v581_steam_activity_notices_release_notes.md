# PAFPlayer V581 — Steam activity notices

Released October 20, 2026.

The console HUD now announces Steam game starts and stops for ten seconds,
including the game name, visualizer frame-budget restriction, and idle-gallery
restriction. The same notice appears immediately below the web song title.
The existing web poll may deliver it up to three seconds after detection;
it displays the remainder of the same ten-second window. Config → Steam
retains the current activity status after the notice expires.

Notices expire during paused playback, including when the FPS HUD is disabled.
Repeated scans and song changes do not restart them. A game already running
at startup is announced. The stop notice occurs when the last game exits.
Help screens, test-tone controls and exclusive warnings retain priority.
Failed/stale scans do not generate a false stop notification. Disabling both
Steam controls disables scans and notices. Other defaults and setting IDs are
unchanged. No additional HTTP polling, playback commands, or hot-path process
scans were added.

## Verification

- 186 relevant checks passed: 14 new transition/HUD/browser checks and 172
  existing Steam, remote artwork, floating lyrics, tray, queue, ownership and
  workflow checks. The browser checks execute the generated JavaScript in Node
  with a controlled DOM and clock, covering expiry, repeated/delayed replies,
  reconnects, hidden tabs, and safe text insertion.
- Three additional historical checks fail identically on untouched V580 and
  V581. Two require obsolete V263–V266 build identifiers; one expects a removed
  frequency-warp choice-button call. They are preserved and are not changes
  introduced by this release. The focused runner excludes those known failures.
- Five Python source/test files and all 24 embedded modules compiled; all eight
  generated web scripts passed Node syntax checks. The release .py is an exact
  SHA-256-verified copy of PAFPlayer.py.
- A real, read-only Windows Steam scan completed without error and reported no
  running game. No real game was started/stopped and the live player was not
  restarted. Visual confirmation in the user's console and browser remains
  manual; see [Steam verification steps](../docs/steam.md#manual-verification).

Reports:

- [189 checks: 186 passing, 3 historical failures](../tests/reports/steam-v581-checks-20261020-065345.json)
- [Same 3 historical failures on V580](../tests/reports/baseline-v580-historical-checks-20261020-065617.json)
- [Compilation, JavaScript and native scan](../tests/reports/v581-build-20261020-065738.json)
- [All affected paths, retained fixtures and verified backups](../tests/reports/v581-change-manifest.json)

## Installation

Restart using the workspace PAFPlayer.py, then refresh the web player. A
non-overwriting standalone release and versioned manual accompany these notes.
No literal C:\BAT path was created, modified, copied, moved or deleted.
