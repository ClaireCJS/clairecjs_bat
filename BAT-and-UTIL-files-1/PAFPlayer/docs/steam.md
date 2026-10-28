# Steam-aware visual load and activity notices (V581)

Web Config now has a **Steam** section near the bottom. Both settings default
on and are saved immediately:

- **Reduce visualizer load by 50% if Steam game is playing** halves the console
  visualizer's current adaptive frame budget (60 becomes 30; 42 becomes 21).
  It affects render deadlines, including live visualizers while paused. Audio
  buffers, playback speed, timed lyrics, and lock-screen timing are unchanged.
  This is a frame-budget reduction, not a promise of exactly half the whole
  player's CPU usage. The browser's separate visualizer retains its own rate.
- **Do not run idle artwork gallery if Steam game is playing** prevents both
  automatic and manually requested idle galleries and ends an active gallery.
  Ordinary album artwork and Floating Lyrics remain available.

Changes apply to the running player; game start/exit detection normally takes
up to two seconds. The section shows the detected game name. Steam being open
alone is insufficient. A running game still counts when minimized, in a menu,
paused, or on another monitor; foreground focus is not required. Settings can
only be changed from the player computer through the existing workflow token
and origin checks. No game is paused, inspected in memory, or controlled.

## Start and stop notices

The console HUD and the web player directly below the song title show a
**10-second notice** when Steam detection changes from no running game to a
running game, and when the last running game exits. For example:

- `🎮 Steam started: RACCOIN · Visualizer 50% · Idle gallery blocked`
- `🎮 Steam stopped: RACCOIN · Visualizer normal · Idle gallery allowed`

The notice names the game and reports the effect of the two current checkboxes.
“Normal” and “allowed” mean Steam is no longer imposing that restriction;
other player settings still apply. An already-running game is announced when
the monitor first detects it. Repeated scans and song changes do not restart
the timer. One game's exit does not announce a stop while another remains.
HUD expiry also works during paused playback and with the FPS display off;
help screens, test-tone controls, and exclusive warnings retain priority.

Both views use the same ten-second detection window. The existing web config
poll can make the web notice arrive up to three seconds later; it shows the
remaining window and expires even if the server disconnects. Browser clock
differences do not affect expiry. Config → Steam keeps the current status
after the notice disappears. Failed/stale scans do not invent a game-stop
notice. With both Steam controls disabled, detection and notices are disabled.

## Detection and limits

One background worker takes a native Windows process snapshot and queries
executable paths with limited access. It matches those paths against Steam's
installed-app manifests, including additional library drives. The inventory is
cached for a minute. Steam's per-app Running registry flags supplement this
when the Steam client is alive, covering some external launchers. Those flags
and manifest layouts are local Steam implementation details, not a guaranteed
public detection API. Installed Steam tools can also count; protected processes,
non-Steam shortcuts, and unusual launchers outside Steam's directories may be
missed. No Steam account, API key, network request, or new dependency is needed.

The rendering thread only reads cached state. A failed or stale scan restores
normal visual budgeting instead of blocking playback. Disabling both settings
stops the process/library scans. A tray-only computer checks games on that
computer for its local idle gallery; the playing computer controls its console
frame budget. Existing configuration IDs are preserved. New internal IDs are
`SteamReduceVisualizerLoad` and `SteamDisableIdleGallery`, stored under the
canonical `Steam` settings subkey.

The native process scan on this computer identified **RACCOIN: Coin Pusher
Roguelike**, with an initial process scan around 37 ms and complete first scan
including the installed-app inventory around 383 ms. These are measurements
from one scan, not a performance guarantee.

Windows APIs: [process snapshots](https://learn.microsoft.com/en-us/windows/win32/toolhelp/taking-a-snapshot-and-viewing-processes)
and [QueryFullProcessImageNameW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew).

## Manual verification

1. Run V581 as the official player; open Web Config → Steam and confirm both
   boxes are checked. With Steam open and no game running, normal FPS remains.
2. Start a Steam game. Within about two seconds the section should identify it
   and the console's target FPS should halve. Audio and lyric timing continue.
3. Disable the first box while the game is running: normal frame budget returns.
   Enable it again, then exit the game: the budget returns automatically.
4. With the second box enabled and a game running, attempt Start idle and wait
   through the configured idle timeout. No gallery should start. Start a gallery
   without a game, then launch the game: the gallery should end.
5. Disable the second box to permit the usual idle behavior. Restart the player
   and verify both saved checkbox choices persist.

6. Launch a game while watching the console HUD and the web song title. Confirm
   the start notice disappears ten seconds after detection, without restarting
   on repeated polls or a song change. The Steam config section stays current.
7. Pause music, disable the FPS HUD, then exit the last game. Confirm the stop
   notice appears and clears ten seconds later without needing a key press.
8. Repeat with one Steam checkbox disabled; confirm the notice describes the
   actual enabled restriction. Check that a help screen or warning still wins.
