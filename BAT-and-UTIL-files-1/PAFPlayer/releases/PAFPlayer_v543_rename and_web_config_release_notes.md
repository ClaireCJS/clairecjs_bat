# PAFPlayer V543 — rename-current-file and Web Config cleanup

Released October 14, 2026.

## Current-file rename

- `F2` prompts for a new filename, preserves the audio extension, renames the current file, updates PAFPlayer's in-memory queue/history references, and resumes from the prior position.
- Playlist repair is opt-in under Playlist. The dependent neighboring-playlist search turns on when current-playlist repair is first enabled, but can be switched off afterward.
- Each playlist changed by the rename receives a verified sibling replacement backup.
- The HUD reports the rename and each playlist being examined.
- Former `F2` karaoke previous is `Ctrl+F2`; former `Shift+F2` treatment previous is `Ctrl+Shift+F2`. The duplicate visualizer alias formerly on `Ctrl+F2` is removed because `F6` and `Shift+M` already provide that action. Megamix moves to `Ctrl+F2+F3`.

## Web and tray cleanup

- Tabs begin Playback, Tags, Metadata / Maintenance; Repair is folded into Playlist and Artwork Actions into Artwork.
- Tags uses Show/Hide wording, beat timing loses its experimental mark and gains suffix spacing, and the progress demo names the demonstrated configuration.
- Experimental headings have an icon, Discord is labeled Discord integration, live logs show newest entries first, and stale tray/lock-screen explanatory prose is removed.
- Global Hotkeys reflects the active player setting and requires confirmation before disabling.
- Raw `\\n` text injected beside the global-hotkey script is eliminated.
- Tray-hover callback failures are caught and sent to the PAFPlayer trace log without console traceback noise.

The standalone tray/web source modules remain development sources; their code is embedded in `PAFPlayer.py`, preserving single-file portability.
