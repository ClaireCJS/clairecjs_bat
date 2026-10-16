# PAFPlayer V523 — household tray controls and native hover card

V523 supersedes the earlier V522 release copy. A 64-bit Win32 callback signature problem found by native hover smoke testing has been corrected; optional tray-only Tk windows now start only when enabled, avoiding a Tcl teardown failure on an idle client. Existing release files were preserved.

## Behavior

- Hovering over either the official or tray-only icon opens a native, non-activating card with artist, track, album, year, genre, song length, and cover art. Cover fetching runs on a worker. The ordinary Shell tooltip stays short and can still show live lyrics when its per-machine option is enabled.
- Double-click either tray button pauses/resumes after the Windows click window. Triple-left selects the previous track; triple-right selects the next track and suppresses the menu. One right-click opens the menu only after the click window expires.
- Tray-only captures Ctrl+Alt+Up/Down with held-key repeat, Ctrl+Alt+A/F for the central art/lyrics windows, Win+C for pause/resume, and physical media play/pause, stop, previous, next, volume, and mute keys. Media previous/next follow the existing player rule: plain keys seek, Shift seeks farther, Ctrl or Alt selects tracks.
- Ctrl+Shift+Alt+A/F and the native right-click menu checkboxes toggle album art and floating lyrics on the tray-only computer. Capture hotkeys is a third per-machine checkbox, enabled by default. Those settings live under the existing TrayMachine HKCU key on that computer.
- Remote lyrics use the central player's lyric timeline and audio-clock timestamp plus a measured server/client wall-clock offset, with interpolation between roughly 250 ms heartbeats. Commands carry their client timestamp and the observed official-owner identity. The client drops commands queued across an owner handoff; the server verifies ownership again before placing any action on the official playback queue.
- The web **Control** section saves `ControlHotkeysEnabled` in the existing global player settings, default enabled. This gates the player's own global shortcuts. Ctrl+Alt+F now toggles floating lyrics on the player computer; the visualizer performance HUD remains available through the web controls.
- The release source copy embeds all updated tray, relay, hover, overlay, machine-settings, and web-workflow modules for single-file use. The current manual and tray/playback guides describe the changed shortcuts.

## Validation

28 tray/instance tests, 9 remote-control tests, 6 V521 live-audio tests, and 6 embedded keyboard tests passed. Nine changed source and test files compiled, and six embedded module sources matched the active files. A native hidden Win32 hover window created, painted cover art, and cleaned up. Older V482 Windows-media tests still fail against the current media implementation and a V416 legacy test cannot import the long-retired `play_audio_file` module; those are outside this tray change.

## Limits

Windows or keyboard drivers may reserve Win+C and physical media keys; polling cannot suppress a media-volume key's normal system-volume effect. Popup placement and repaint timing depend on Explorer. Lyric clocks align approximately, but network delay, thread scheduling, and display refresh prevent sample-accurate simultaneity. A forced termination may leave a stale Explorer icon until the shell refreshes; normal shutdown removes the icon and closes local windows. The remote client requires the existing web server to be reachable on the household LAN.
