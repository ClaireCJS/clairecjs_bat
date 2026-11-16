# PAFPlayer V686 — Playlist editor interaction

The playing marker now uses a fixed-width character to keep the track-number column aligned. Drag a row to change the active session playback order. Like the existing console-browser move, it changes the session and shuffle cache without rewriting the playlist file. A snapshot guard rejects a drag if the playlist changed before the player processes it.

Press J in the playlist window for a live, playlist-scoped search; Enter or double-click plays the selected result. The search considers path, filename and loaded artist/title labels, with multiword filtering. Metadata and duration are read in the background, updating rows and search results as tags arrive; missing tags fall back to filenames. Selection and scroll position are preserved during background updates.

Focused tests exercise duplicate-preserving reordering, metadata fallback, and real Tk drag and J interactions in an isolated player window, alongside existing playlist, lifecycle, and bundle-parity checks.
