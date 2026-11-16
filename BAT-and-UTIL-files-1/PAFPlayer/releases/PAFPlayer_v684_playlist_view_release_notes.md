# PAFPlayer V684 — Playlist window

Alt+P toggles a compact playlist editor while a playlist is active. The window shows numbered rows, a current-track marker, selection, scrolling, and background duration lookup. Double-click or Enter plays a selected track; selection alone does not alter playback. Add files or recursive folders with the buttons or Windows Explorer drag-and-drop. Delete offers a saved removal, a session-only removal, or cancellation. All changes use the existing player playlist operations and play-next rules. Closing the window shows a HUD notice for approximately 30 seconds.

The window uses native controls with a classic Winamp-inspired palette; it does not load Winamp skins or implement every classic menu or reordering gesture. Duration metadata requires Mutagen and a readable duration. File drops use native WM_DROPFILES, not an optional drag-and-drop package. PLS and XSPF additions create verified replacement backups before rewriting the playlist.

Verification: focused V684 tests and single-file source parity; Alt+P console mapping; a Windows native-window open/close smoke test; and a synthetic WM_DROPFILES message carrying an existing audio file. A physical Explorer drag and complete playback session still require interactive verification.
