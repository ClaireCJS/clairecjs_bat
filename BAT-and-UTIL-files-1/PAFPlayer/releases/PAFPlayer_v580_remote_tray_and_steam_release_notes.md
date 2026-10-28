# PAFPlayer V580 — remote tray artwork, Options, and Steam-aware visuals

Release date: October 19, 2026. Base: V579. Existing configuration IDs and
single-instance/test isolation behavior are preserved.

## Changes

- Web Config → Steam adds two saved, default-on checkboxes: halve the console
  visualizer frame budget while a Steam game runs, and suppress idle artwork
  galleries during that time. Detection uses a background Windows process and
  Steam-library scan. Audio playback and lyric clocks are unchanged.
- Remote artwork uses the full native artwork/lyric renderer and inherits server
  appearance by default. A server/on/off selector controls lyrics over artwork
  independently of the Floating Lyrics window. Canonical registry names are
  translated back to the existing renderer IDs; placement and visibility stay local.
- Both trays expose Options. Remote Options contains local display/hotkey/hover/
  wallpaper/icon controls, inheritance, artwork lyrics, native appearance editors,
  and centering. It shares the renderer's Tk interpreter and thread.
- Tray-only launches return the shell immediately after starting a detached
  child. Diagnostics go to unique per-user logs. Reload creates another detached
  child; Exit closes local resources. Add `--foreground` for attached diagnostics.
- The two-choice Emoji coloring dropdown is documented as a TODO for both player
  and tray. Floating Lyrics stability is user-confirmed; physical remote-machine
  Whip rendering remains unconfirmed.

## Verification

- **172 tests passed**, zero failures/errors/skips, including Steam transitions,
  saved preferences, render-only budgeting, idle suppression, endpoint protection,
  inherited presentation/override behavior, existing MonkeyMote multi-client and
  queue tests, remote Save As, tray native APIs, and floating-lyric regressions.
  [Final test report](../tests/reports/remote-v580-checks-20261019-235509.json).
- **14 Python files and all 24 embedded modules compiled**; all six modified
  bundled modules match their reviewed external sources. **Eight web JavaScript
  blocks passed Node syntax checking.**
  [Build report](../tests/reports/v580-final-build-20261019-235527.json).
- A real isolated `--no-tray` player and `--tray-only --foreground` client ran
  together with timed lyrics and cover art. Both windows stayed visible, Options
  opened/closed, the artwork lyric override switched off/on, and a live server
  color-mode change reached the client. Both processes exited 0 without recorded
  callback/interpreter errors. [Native run](../tests/reports/remote-artwork-v580-20261019-162152-processes.json).
- A real detached native tray returned the launching process in about **1.98 s**,
  reloaded, and exited 0. Its console window handle was zero both before and after
  Reload. [Launch/Reload/Exit report](../tests/reports/background-tray-v580-20261019-235404.json).
- Native detection identified **RACCOIN: Coin Pusher Roguelike** on this computer.
  Twelve repeated process scans took about 32–35 ms each and left handle count
  unchanged at 171. [Scan report](../tests/reports/v580-build-20261019-162505.json).

These are focused and relevant tests, not a claim that the entire historical
suite was run. Native window-state samples are not screenshots. Physical remote
computer appearance, unusual/protected Steam launchers, and long gaming-session
performance still require observation. Steam tools may count as running apps;
Steam simply being open does not. Frame budgeting halves visual work frequency,
not necessarily total application CPU usage.

## Use and manual checks

Restart the player and update/restart its remote tray with V580. Defaults are
active automatically. See [Steam configuration and limits](../docs/steam.md),
[tray configuration](../docs/windows-tray.md), and the
[manual verification procedure](../docs/PAFPlayer_v580_remote_tray_and_steam_manual.md).
The web/remote port remains 666 by default and supports `--web-port=PORT`.

The source and immutable release were saved in the project workspace. No literal
`C:\BAT` path was created, modified, copied, moved, renamed, or deleted.
Replacement backups were created and hash-verified before every overwrite.
See the [complete retained-path manifest](../tests/reports/v580-change-manifest.json)
for source, documentation, tests, backups, release artifacts, and isolated fixtures.
