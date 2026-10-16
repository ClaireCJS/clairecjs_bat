# PAFPlayer V544 — profile activity, ordered help, and pictorial tray gallery

Released October 14, 2026.

- The native right-click tray picker contains 50 choices, displays an icon preview beside every description, and uses ten rows across five columns. Icon bitmap rows use the correct Windows bottom-up orientation.
- Tray, hover, workflow UI, and Discord code remain embedded inside `PAFPlayer.py`; standalone modules are development sources and are not required beside the portable player.
- Bare Shift, Ctrl, or Alt switches the console help overlay between section view and a colored one-binding-per-line view ordered A–Z, F1–F10, then other keys.
- `Shift+F2` is the preferred previous karaoke-treatment key. `Ctrl+Shift+F2` remains an alias.
- Discord integration uses local Discord Rich Presence to update the user's profile. The Web Config takes a Discord Application ID; channel webhooks, webhook credentials, and channel posts are removed from the active workflow.
- The progress demo label names Style 1, Spectral Flux, Beat illumination, and Flash Full.
- V543's Web Config cleanup remains covered: Playback → Tags → Metadata / Maintenance, Show/Hide tags, spaced beat-timing units, newest-first live logs, Global Hotkeys confirmation, and removal of the literal `\\n\\n` fragment and unwanted status prose.
