# Windows tray icon (V626)

## V626 tray-icon file drops

Drag audio files or a folder from Explorer directly onto the PAFPlayer tray
icon to enqueue them. This also works on a tray-only computer: its tray sends
the drop to the verified central player, which resolves the files against its
own library. The icon remains owned by its existing official or remote tray
process. Explorer draws notification-area icons, so PAFPlayer briefly places a
nearly invisible drop target over its own icon while a held drag approaches.
The target disappears after the drop or release; normal click-sequence actions
continue through the same tray handler. Folder expansion and queue placement
use the existing enqueue rules. A remote drop requires the server to recognize
the files; it does not upload their bytes. Windows Explorer delivery and the
notification-area overflow should be checked on the target machine.

## V624 remote Pause controls

The physical **Pause** key and **Media Play/Pause** key on a tray-only computer
send the central player one pause toggle per press. Holding either key does not
repeat, and simultaneous reports of both keys produce one toggle. The tray's
existing Play/Pause menu action and double-click use the same remote command.

## V625 remote window file drops

Drop an audio file or folder onto artwork or Floating Lyrics on a tray-only
computer to enqueue it on the central player. The client expands a folder's
immediate audio files, then sends filename, trailing folders, and file size as
matching hints. The official player verifies its owner identity and resolves
them against its library; an ambiguous or missing match is rejected. The
client does not start its own playback or use its local drive letter as a
server path. V626 also accepts the drop directly over the tray icon.

## Remote `en` from a tray-only computer

Starting `PAFPlayer --tray-only HOST:PORT` remembers that server in
`%APPDATA%\PAFPlayer\RemoteTray\last-server.json`. With
`MUSIC_PLAYER=PAFPLAYER`, `en "Song.flac"` asks the official server to find and
queue that song. `en re:"artist/.+title"` searches the server's music library;
`en --server HOST:PORT ...` chooses a different server for one request.
Different client drive letters are resolved by filename, trailing folders and
file size when available. The server rejects ambiguous results. See
[remote enqueue](remote-control-api.md#v615-remote-enqueue-and-library-search).

## V613 tray-only artwork and lyric hotkeys

On a `--tray-only HOST:PORT` computer, `Ctrl+Alt+A` shows and raises the **local**
album artwork window; `Ctrl+Alt+F` shows and raises the **local** Floating Lyrics
window. Repeating either shortcut raises the same window without hiding it.
Adding Shift keeps the same local behavior. These shortcuts never send an
artwork or lyric command to the playing computer. The tray's right-click
checkboxes still explicitly turn the local windows on or off.

Each server's tray icon, hotkey capture, local window visibility, artwork and
lyric appearance, geometry, tooltip, and wallpaper preferences are saved in
that client's `%APPDATA%\PAFPlayer\RemoteTray\tray-<server-hash>.json` file.
The tray's **Options…** window shows the exact file and can open its folder.
To move preferences to another computer, exit the tray there, copy the matching
JSON file into that computer's `%APPDATA%\PAFPlayer\RemoteTray` folder, and
start `--tray-only` with the same hostname and port. Copy all `tray-*.json`
files to carry choices for several servers. Screen coordinates, download
folders, and any saved wallpaper paths may need adjustment on the new computer.
The file is local to the client; no local desktop preference is written to the
music server.

## V596 emoji coloring selector

The player's Artwork and Floating Lyric Coloring windows and each tray's
**Options…** window now have an **Emoji coloring** dropdown. It has exactly
two choices: **Official color emoji — no additional coloring** and
**Monochrome emoji — {current treatment}**. The second label follows the
selected pattern treatment, per-letter palette, or solid color mode; changing
it selects the rendering type without changing the coloring treatment or its
saved mode ID. The choice applies to artwork and Floating Lyrics together,
and the existing small emoji button in the artwork title bar stays in sync.
The official player uses its existing saved preference. A `--tray-only` client
stores a local choice for its remote server through its existing presentation
settings; selecting a local appearance stops following server appearance
until **Follow the server's artwork and lyric appearance** is re-enabled.

## V580 options, inherited artwork, and background launch

**Options…** in either tray's right-click menu collects the tray's machine
switches, full-information hover preference, and icon selection. The official
tray also exposes its saved enable preference. The remote tray adds artwork
and floating lyric visibility, hotkey capture, server appearance inheritance,
artwork lyric selection, native appearance editors, and centering buttons.
Options shares the artwork renderer's Tk thread and interpreter; opening it
must not interrupt or hide either display.

Remote artwork now uses the same `ExternalAlbumArtWindow` renderer as the
player, including timed lyrics, Emojimaxx, coloring, solutions, and artwork
variants. **Follow the server's artwork and lyric appearance** is on by
default. Live server preference changes are picked up in roughly one to two
seconds. Canonical registry names are mapped back to stable renderer IDs.
Placement, size/geometry, visibility, and endpoint settings remain local.
Editing a local appearance setting stops following the server; re-enable
Follow to inherit again.

**Lyrics over album artwork** offers **Use server setting**, **On**, and
**Off**. This local override is independent of Floating Lyrics visibility and
does not change anything on the playing computer. Preferences remain in the
existing per-server `%APPDATA%\PAFPlayer\RemoteTray` JSON. An older server
that does not publish appearance preferences falls back to local defaults.

`python PAFPlayer.py --tray-only HOST:PORT` now launches a detached background
tray and returns control to the shell. Right-click **Exit this tray** closes
the client, its windows, and network workers without sending output to the
launching console. Startup prints the child PID and unique diagnostics log
under `%APPDATA%\PAFPlayer\RemoteTray\logs`. That message means startup was
requested; a startup failure is recorded in the log. Use
`--tray-only HOST:PORT --foreground` to keep diagnostic/test runs attached.
A background Reload launches another detached tray with a new log; a
foreground Reload stays attached. Neither attaches a new console. There is still only one remote tray
per Windows logon session.

Floating Lyrics stability is user-confirmed; Whip's physical remote-client
appearance remains unconfirmed.


## V577 remote Save As

On a `--tray-only HOST:PORT` computer, the right-click menu includes **Save
current music file…**. It opens the Windows Save As dialog with the source
filename and extension filled in, then shows transfer progress and a completion
or error message. The tray-only computer saves one file locally; it does not
alter playback or copy a playlist. If the selected destination exists, the
transfer refuses to overwrite it.

The request carries the official instance identity, the exact source path, and
a logical track-visit number. The server checks these before opening the file
and during streaming; the client checks again before making the completed copy
visible. An owner change, skipped track, interrupted transfer, or short response
fails the save. Incomplete copies are sent to the Recycle Bin; if recycling is
unavailable, the partial file is retained and its location is reported.

Successful destination folders are remembered per remote server in its existing
`%APPDATA%\PAFPlayer\RemoteTray` settings. Save As starts in the most recently
used folder that still exists, then the next existing folder, then Downloads or
the user's home directory. This feature uses the configured household HTTP
connection, so use it only on a trusted network.

V563 removes the tray-only floating lyric window that used a separate plain Tk
label. Remote floating lyrics now instantiate the player's own
`ExternalAlbumArtWindow` and feed it the remote server's timestamped lyric,
progress, track identity, speed, and transport state. Consequently the local
and remote screens execute the same glyph-mask, karaoke color, EmojiMaxx,
teeny-solution, autosize, transparency, click-through, positioning, editor,
and animation code. Only persistence differs: in tray-only mode the renderer's
existing preference calls—and the tray-only presentation switches—are
redirected to that server's JSON under
`%APPDATA%\PAFPlayer\RemoteTray` rather than the playing computer's registry.

V562 adds **Reload tray from updated PAFPlayer.py** to the tray-only client's
right-click menu. It shuts down the current icon, local overlays, wallpaper
lease, and server connection, releases its Windows ownership mutex, then
replaces itself using the current main `PAFPlayer.py` file. This is intended
for picking up a background file update without leaving competing tray clients.
Only one tray-only client is permitted in a Windows logon session; a second
launch exits cleanly. The single-file player contains the tray implementation
in its embedded source bundle. The similarly named files in the source tree
are development/build inputs used to regenerate that bundle, not files loaded
by a shipped standalone `PAFPlayer.py`.

Tray-only icon style and full-information-tooltip choices are saved separately
for each normalized remote server under `%APPDATA%\PAFPlayer\RemoteTray`. They
are not written beside `PAFPlayer.py`. Consequently, changing the icon from a
remote tray's native chooser persists through its two-second refresh and later
restarts without borrowing another server's selection.

V555 renders the native chooser's pictorial previews at the same 32×32 canvas
for which the symbols were designed, avoiding the old upward/right clipping.
It also accepts both legacy and packed notification-area mouse events, so the
enabled full-information card reliably appears after a 0.666-second hover.

V551 provides 20 genuinely different icon types, each in 10 colorways, for
200 combinations. The native chooser groups these as type → color so it stays
usable on screen. Since V585, Web Config also presents separate groups of 20
icon types and 10 colors instead of the old 200-item gallery. All indices
0–199 remain valid saved choices; the old 0–19 validation limit no longer
causes later choices to revert on the tray's periodic refresh.

The right-click **Full info on tooltip** option is persistent and off by
default. When enabled, leaving the pointer over the icon for 0.666 seconds
opens the click-through album-art and full track-information card. Clicking or
moving away cancels/hides it, keeping the icon available for normal clicks.

Icon selections from either the native right-click chooser or Web Config are
saved immediately and sent to the live tray. Web requests wait briefly for the
tray thread to acknowledge the new icon. If Windows Explorer rejects an icon
modify during a tray rebuild, PAFPlayer deletes and re-adds its notification
icon with the requested artwork instead of leaving the stale image visible.

PAFPlayer enables one Windows notification-area icon by default. The official instance owns it. The tooltip identifies the official process by version and PID, without showing media paths or credentials.

## V541 icon gallery and safer artwork hover

Web Config's **Windows tray icon** section now includes 50 built-in icon designs. Selecting one saves it immediately as `TrayIconStyle`, updates the official tray without restarting PAFPlayer, and keeps that choice for later runs. The same designs are available under **Choose tray icon** in the tray icon's right-click menu. Each native menu row displays a correctly oriented preview beside its description; ten rows per column produces a compact five-column picker, and the check mark identifies the current choice.

The artwork hover card now requires a deliberate 700 ms hover. It is positioned above or below the actual Windows notification-icon rectangle with a gap, clamped to the desktop work area, and is click-through. It therefore cannot cover or intercept the icon while the user is trying to right-click it.


## V522–V523 household controls and hover card

V523 corrects the 64-bit Win32 hover callback signature found in the V522 artwork smoke test.

V524 also resets the process-global `RegisterClassW` ctypes prototype immediately before registering the hover window. The main tray and hover modules intentionally declare their own local `WNDCLASSW` structures; without this reset, loading the main tray first could make `--tray-only` fail with an `expected LP_WNDCLASSW` type error before its icon appeared.

Hover over either the official icon or a tray-only icon to see a native popup with artist, track, album, year, genre, duration, and current cover art. The card is drawn by the existing tray Win32 message thread; artwork is fetched on a worker so it cannot stall the icon, player, or console. A normal Shell tooltip remains short because Windows notification tooltips cannot embed pictures. Album art may appear shortly after the text while the server extracts it. The popup contains no audio path, credential, or token.

A tray-only machine captures these controls when **Capture control hotkeys here** is checked (the per-machine default):

- `Ctrl+Alt+Up/Down`: adjust the playing computer's volume; a held key repeats after 320 ms, then about every 85 ms.
- `Ctrl+Alt+A` and `Ctrl+Alt+F`: show and raise album art and Floating Lyrics on **this tray-only computer**. Repeated presses leave them enabled. Adding Shift is an alias.
- `Win+C`: pause/resume the playing computer. The physical media play/pause and stop keys also relay. Media previous/next seek by 10 seconds (80 with Shift); adding Ctrl or Alt selects previous/next tracks, matching the player. Media volume and mute keys relay too. Some keyboards or Windows shells may consume or duplicate these hardware/system shortcuts before PAFPlayer can observe them.

The local floating lyrics use the current server lyric timeline, its audio-clock timestamp, and the measured server-to-client wall-clock offset. Tray-only clients refresh the server heartbeat about four times per second. Paused lyrics freeze; normal playback is extrapolated between updates to keep nearby screens aligned. Windows task scheduling, network delay, and each monitor's refresh rate can still create visible differences of tens or hundreds of milliseconds; this is not sample-accurate synchronization. Control commands carry their client timestamp and are accepted only if the server's official owner identity still matches. They are executed in that owner's queue, never by a background playback instance.

The web configuration **Control** section contains **Enable Windows control hotkeys on this player**, saved in the existing global player registry as `ControlHotkeysEnabled` (default enabled). The tray-only machine's capture switch is separate and stored alongside its other local tray options. Unchecking the player setting disables its own global chords; it does not disable commands intentionally sent from an authorized household tray. `Win+C` can be reserved by some Windows 10 builds, so availability depends on the local shell.

## Clicks and menu

- Triple left release: previous track.
- Triple right release: next track and suppress the menu.
- Double-click either button: toggle Play/Pause after the click window expires. A third click takes precedence, so a triple-click never also toggles playback.
- Single right release: open the menu after the click window expires. This delay lets a second or third click arrive without opening an unwanted menu.

The click window follows the Windows double-click time, clamped to 350–900 ms. PAFPlayer counts button releases by monotonic timestamp, not Windows double-click messages. The menu offers Play/Pause, Previous track, Next track, Open web configuration, **Choose tray icon** (20 types and 10 colors), Open tag viewer, local presentation options, Open current track folder when available, About/version, and Exit. Playback commands enter the same queue used by the web controls; they do not change keyboard shortcuts or queue rules. The tray message thread does not run audio playback.

## Options on each computer

The official tray and every `--tray-only` client have **Show sung lyrics above tray** and **Album art desktop wallpaper** switches in their right-click menus. Both start off. The official tray stores these choices for the current Windows user under `HKCU\Software\ClaireCJS\PAFPlayer\TrayMachine`. A tray-only client stores them in its per-server roaming AppData JSON alongside its other local options. Switching either option does not write a preference to the remote server.

The lyric tooltip uses the current lyric already published by the owner. Each changed, nonblank sung line appears automatically in a wide bright-yellow PAFPlayer bubble immediately above the actual notification-area icon; hovering is not required. This is not a Windows notification and does not enter Notification Center. The bubble is non-activating and click-through, remains clear of the icon, follows taskbars on any screen edge, stays on the current lyric while paused, and hides when lyrics are blank, the option is disabled, the icon disappears, or the server disconnects. Remote clients poll about every 0.4 seconds while this option is active. The desktop option gets the owner's current artwork and makes a centered BMP sized for this computer's primary display. Its worker changes only the local desktop wallpaper, never the lock-screen background. It restores the prior picture path on disabling the option, losing the track, disconnecting, or closing the tray normally, as long as the user has not changed the wallpaper in the meantime. Windows slideshow/theme mode and per-monitor choices are not restored; the generated image is sized for the primary display. A named Windows mutex lets only one PAFPlayer tray on the same desktop drive the wallpaper. A crash may leave the last artwork until PAFPlayer runs again or the user changes the wallpaper. The artwork cache is under `%LOCALAPPDATA%\PAFPlayer\TrayWallpaper`; old generated images are sent to the Recycle Bin when `send2trash` is available, and otherwise retained rather than permanently deleted.

The playing computer must run V504 or newer for remote wallpaper rendering. The remote tray-only computer needs no Pillow installation; the player server renders a bounded BMP. These options never change the audio file or its embedded art.

## Native tag viewer

Choose **Open tag viewer** to open PAFPlayer's own Windows window, with Overview, Tags, Lyrics, Artwork and Technical tabs. It lists the current file path, size and duration; readable tags from the existing all-tags browser; parsed lyrics from sidecars or embedded metadata; each available artwork image; and FFprobe container, stream and chapter details. The viewer follows track and artwork changes and has a manual Refresh button. Binary frames and audio samples are summarized or shown as images rather than dumped as text. The viewer is a separate process so its Tk window never blocks audio or the tray's Windows message loop.

The viewer uses the owning player's read-only `/api/track-details` and `/api/track-details/art` endpoints. If `--no-web-server` is active on the player, the menu explains that the viewer requires the web server; it does not override the command-line setting.

## Tray-only clients on other Windows computers

On each other computer, run `PAFPlayer.py --tray-only machineservername:666` (or the current single-file release with the same arguments). This starts only a remote tray client: no audio, local official-instance claim, playback queue, or duplicate official icon. Its tooltip identifies the target server and connected/disconnected state. A Windows mutex permits only one remote tray client in the same logon session. If the server disappears, the icon remains clearly disconnected and retries its `/api/remote-tray/hello` heartbeat. That response identifies the current official owner; each playback request includes its identity and the server rejects a request if ownership changed. Remote clicks and menu commands go only to the named official server; **Reload tray from updated PAFPlayer.py** restarts this tray from the current single file, while **Exit this tray** stops only this client's icon. Its **Open tag viewer** opens the same native window and fetches that server's metadata and artwork.

The playing computer must bind its existing web server to a LAN address, for example `--web-host=0.0.0.0 --web-port=666`, and allow the port through its Windows firewall. The default loopback bind cannot be reached from another machine. This is plain HTTP and the existing LAN control endpoints do not require pairing, so expose the port only on a trusted household network. The tray-only client does not change the server's bind setting or saved preferences.

## Settings and instances

`TrayIconEnabled` is an existing global player-registry DWORD setting, defaulting to 1 when absent. `TrayIconStyle` is a zero-based built-in design index, defaulting to Violet Play. The web configuration's **Windows tray icon** section changes both saved preferences. The status explains whether this process is the official owner, and reports when a command-line override applies. Changes made from an additional instance are global; the official tray refreshes within two seconds.

`--tray` and `--no-tray` override the saved preference for the current run only. Neither switch rewrites the registry. `--instance` allows an additional playback process. It does not take the official icon while the official mutex is held. A normal second launch still forwards its validated media request through the authenticated local IPC server and creates no icon.

When the official instance exits, an additional instance polls and competes for the same named Windows mutex. Only the winner starts the official IPC endpoint and icon. The old `instance.json` PID is not treated as proof that an owner is alive. The owner cleans up its notification-area icon on normal shutdown and re-adds it after Explorer restarts. A sudden process or Explorer failure can leave a temporarily stale shell display until Windows refreshes the notification area.

The menu's web and viewer entries require the web server to be enabled for the owning process. The current-track folder entry is disabled when there is no current track. Multiple `--instance` processes may continue playback independently, but only the current mutex owner exposes the official tray controls. Explicit tray-only clients are separate, labeled remote controls of that owner.
