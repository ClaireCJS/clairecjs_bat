# PAFPlayer V613 — tray-only local artwork and lyric hotkeys

On a tray-only computer, `Ctrl+Alt+A` shows and raises the local album art
window and `Ctrl+Alt+F` shows and raises local Floating Lyrics. Repeated presses
raise the window without hiding it. The Shift variants do the same. Right-click
checkboxes still provide explicit on/off control. These hotkeys never send the
window action to the music server.

The client keeps each server's machine options and renderer preferences in its
existing `%APPDATA%\PAFPlayer\RemoteTray\tray-<server-hash>.json` file. Options
now shows the exact file and opens its folder, so the JSON can be copied to a
future computer. Copy the file while that tray is stopped and use the same
server hostname and port. Display geometry, saved download folders and wallpaper
paths may need adjusting on the new computer.

Focused regression tests cover hotkey routing, repeated show requests and
per-server JSON portability. A physical tray-only client with Windows desktop
focus behavior still needs a live UI check.
