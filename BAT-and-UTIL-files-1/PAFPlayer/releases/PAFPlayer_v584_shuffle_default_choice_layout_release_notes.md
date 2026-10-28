# PAFPlayer V584 — shuffle lifetime and compact choice tools

The factory/default **Fresh shuffle after** value is now 72 hours (4,320
minutes) instead of 5 hours. Existing explicitly saved values remain respected;
using the control's default restores 72 hours.

Web configuration choice tools now keep Fav, Def, and the associated cycle
button on one horizontal line. The cycle button is always placed to their right,
avoiding an extra vertical row.

The Floating Lyrics **Display song title for first** duration now keeps its
editable numeric textbox immediately to the right of the slider, followed by
the seconds unit, all on the same row.

The main Playlist panel now contains playlist behavior and repair options rather
than thousands of track rows. **View playlist** opens the active list and its
existing queue/removal/reload tools in a separate tab. Playlist repair now says
that F2 path replacements affect the active playlist and, optionally, sibling
playlist files—not unrelated audio or the whole library.

The experimental console-title tester now uses separate **Title type**, **Title
coloring**, and **Title content** dropdowns. Each receives the standard Fav,
Def, and cycle controls. Content choices are PAFPLAYER, NOW PLAYING, and MUSIC.

Saving a default playback-device combination now catches Windows REG_DWORD
overflow and still writes the durable JSON fallback, so large multi-device masks
remain the selected default.

Tray Options now includes a 64–400 px hover-art slider and a preview square that
resizes continuously with it. The selected size is persisted per player/tray
preference backend and applied to the actual full-information hover card.

Windows Lock Screen configuration now detects the installed companion version,
offers **Install / repair integration**, and gives specific enable-UAC-and-reboot
guidance only when Windows reports UAC disabled. **Test Lock Screen Now** asks
for confirmation and then locks the workstation immediately.

Folder Monitoring now explains Index, Library, Playlist, Recursive, Pause,
Resume, Scan, and Dry-run behavior. Its results start inside a collapsed details
panel, and the copy makes clear that monitoring does not rename, retag, move, or
delete audio files.
