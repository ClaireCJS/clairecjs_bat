# PAFPlayer V701 release notes

## Web layout

- Removed the rainbow song-title backdrop and replaced it with a neutral translucent backdrop that lets the page artwork remain the visual gradient.
- Put the filename, wrapping status bubbles, and URL area into one compact responsive header row.
- Moved the web visualizer on/off switch directly above Web Karaoke; the Web Karaoke tab now opens that combined area.
- The configuration panel is closed by default. A bottom-right gear button enables or disables it, with the browser choice remembered.
- Moved metadata/maintenance and tag controls into the bottom of Playback instead of giving them separate tabs.
- Reordered the configuration tabs, placed Windows / Lock Screen after Console Visualizer with an emoji, and added consistent emojis to Steam, Last.fm, MonkeyMote, and Monitoring.
- Steam controls now use the same colored toggle cards as other settings.

## Tray discovery

`--tray-only` may now omit `HOST:PORT`. The client searches private local `/24`
IPv4 networks, probes the web interface port 666 and MonkeyMote port 19371,
verifies PAFPlayer HTTP identities on web responders, and prompts the user to
choose a verified player. Explicit `--tray-only HOST:PORT` behavior remains.

## Steam pacing verification

The Steam reduction option is not cosmetic. `Monitor.visualizer_fps()` returns
50% of the target while a detected Steam game is running, and the player uses
that value when scheduling its visualizer deadlines. Audio and lyric timing are
not routed through this reduction.

## Clarification

“Spaced style modifier” adds spacing to the selected Web Karaoke style.
“Framed style modifier” adds the selected frame treatment around that style.
They are functional Web Karaoke modifiers, not unused placeholders, so V701
keeps them available.

## Verification

- Active and release sources are syntax-checked.
- Bundled Steam, Windows UI, and remote-tray sources are synchronized with their editable modules.
- Embedded V701 web-layout/LAN-tray contract tests cover the new controls and discovery source.
