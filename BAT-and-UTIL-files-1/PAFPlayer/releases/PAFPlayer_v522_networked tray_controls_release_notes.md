# PAFPlayer V522 — household tray controls

## What changed

- The official tray and `--tray-only host:port` icon show a native mouseover card with artist, track, album, year, genre, length, and current cover art. The short Windows tooltip remains available, including the optional live lyric. Artwork loading happens off the tray message thread.
- Double-click still toggles Play/Pause after the 350–900 ms click window. Triple-left goes to the previous track; triple-right goes to the next track and suppresses the menu. A single right-click opens its menu only after the window expires.
- Tray-only clients can capture Ctrl+Alt+Up/Down volume (held key repeats), Ctrl+Alt+A/F for the player computer's art and lyrics windows, Win+C for pause, and media transport, seek, volume, and mute keys. Ctrl+Alt+MediaPrevious/Next selects tracks. Actions pass through the existing official-owner HTTP relay and playback queue.
- Ctrl+Shift+Alt+A/F and matching right-click checkboxes show local art and floating lyrics on the tray-only computer. These options and the remote hotkey capture switch are saved per Windows user on that machine under the existing TrayMachine registry key. Remote lyric text uses the server's published audio timestamp and a measured clock offset, interpolated between heartbeats.
- The web configuration has a **Control** section with a saved **Enable Windows control hotkeys on this player** checkbox, default enabled. The setting uses the existing global registry store as `ControlHotkeysEnabled`. The official player uses Ctrl+Alt+F to toggle its floating lyrics and Win+C to pause/resume.
- Each remote action carries a client timestamp and the official instance identity. A queued action is discarded if the owner changes before transmission; the server independently verifies its official owner before enqueuing. An explicit additional `--instance` remains separate from tray-only control and cannot hijack the official icon.
- The standalone V522 release copy embeds the updated tray, relay, hover, overlay, machine-settings, and web-workflow modules.

## Validation

Focused V522 controls and owner-handoff tests, existing V499/V503/V504 tray tests, V521 audio controls, and Python compilation were run. The older V482 Windows-media test module has pre-existing expectations that conflict with the current Windows-media implementation; see final test report.

## Limits

Windows may reserve Win+C or a hardware media key, and GetAsyncKeyState cannot suppress a key's normal system-volume effect. The popup's exact position and repaint timing depend on Explorer. Remote lyric windows synchronize to the reported audio clock but network delay, thread scheduling, and monitor refresh are not sample-accurate. A forced process termination can temporarily leave an Explorer tray image or local presentation window until Explorer refreshes or the client restarts; normal shutdown removes them. `--tray-only` still requires the player's web server to be reachable on the trusted LAN.
