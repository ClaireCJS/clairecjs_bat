# PAFPlayer V625 — tray-only window file drops

Released October 27, 2026.

- Artwork and Floating Lyrics windows on a tray-only computer now send dropped files and folder contents to the official central player through the remote enqueue API. The tray-only process does not start local playback.
- The client sends path hints and file sizes; the server matches them in its own music library, so different drive letters can work. Missing or ambiguous matches are rejected. The request includes the verified official instance identity, preventing an ownership change from silently directing a drop elsewhere.
- This path does not upload file bytes. The server must already have the music indexed. Windows notification-area icons themselves are not file-drop windows; use the artwork or lyric window, web page, or `-q` for drag/drop or enqueue work.

Verification: focused remote-window-drop tests, existing tray and queue tests, Python syntax checks, and bundled-source parity. Explorer shell delivery and a real cross-machine drop still require a Windows desktop test.
