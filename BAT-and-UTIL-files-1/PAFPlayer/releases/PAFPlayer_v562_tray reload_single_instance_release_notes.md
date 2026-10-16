# PAFPlayer V562 — tray reload and single-instance hardening

- Adds **Reload tray from updated PAFPlayer.py** to the remote tray menu.
- Reload closes overlays and connections, releases ownership, and replaces the
  process from the current portable player file.
- Allows only one tray-only client per Windows logon session.
- Prevents missing optional log callbacks from escaping a native Win32 callback.
- Declares 64-bit window-handle types before destroying lyric and hover popups.
- Persists each remote server's tray icon/settings under roaming AppData rather
  than beside the portable player.
- Keeps the shipped tray implementation embedded in the single `PAFPlayer.py`.
