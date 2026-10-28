# PAFPlayer V626 — tray-icon drops and available-memory buffering

Released October 27, 2026.

- Audio files and folders dragged from Explorer onto the notification-area icon enqueue through the official player's normal queue path. A tray-only client's icon sends the drop to its verified central server; the server resolves filenames and folders in its own library, without starting client playback or uploading file bytes.
- Explorer owns the actual notification-area icon, so PAFPlayer temporarily places a nearly invisible, non-activating Windows file-drop target over the icon while a held drag approaches. It removes the target after the drop or release and forwards a captured button release to the existing click-sequence handler. The target is created only for an icon with a valid drop reader and callback, and is destroyed on tray shutdown.
- Whole-file memory playback has no fixed 64 MiB limit. For each track, PAFPlayer checks available physical, commit, and virtual memory and reserves at least 1 GiB or one eighth of installed RAM, whichever is larger. If the file does not fit or cannot be read, it plays from disk. When memory buffering succeeds, the original file is closed before the decoder uses the seekable loopback source.
- The existing V556 tray tests now read source from `src/`, and the V624 simple-player test fake accepts optional tray constructor parameters.

Verification: six focused V626 tests, 79 tray tests, existing V624 memory/drop and simple-instance tests, relevant playlist and V625 remote-drop tests, Python syntax checks, and bundled-source parity. A 65 MiB synthetic track buffered successfully. A physical Explorer drop onto both a visible and overflow tray icon, including on a second machine, still needs a Windows desktop check; no automated test can prove Explorer's cross-process drag delivery here. Memory buffering does not remove file locks held by other programs.
