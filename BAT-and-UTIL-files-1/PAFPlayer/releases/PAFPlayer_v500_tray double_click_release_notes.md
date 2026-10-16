# PAFPlayer V500 — tray double-click Play/Pause

Double-clicking either mouse button on the Windows tray icon now toggles Play/Pause through the owning instance's existing playback command queue. The action waits until the Windows click-sequence window expires, so a third left click still selects the previous track and a third right click still selects the next track without also toggling playback. A single right click still opens the context menu after the same delay. The click window follows the Windows double-click time, clamped to 350–900 ms.

All V499 tray ownership, `--instance`, `--tray`/`--no-tray`, saved setting, web configuration, menu, and shutdown behavior remains in place. The single-file release includes the updated tray module.
