# PAFPlayer V499 — Windows tray icon

- The Windows tray icon is enabled by default. Triple left-click selects the previous track; triple right-click selects the next track. Both use the existing playback action queue.
- Each click sequence uses monotonic timestamps and the Windows double-click interval, clamped to 350–900 ms. A single right-click opens the context menu only after that interval expires. A triple right-click suppresses the menu. Double-click is a no-op.
- The menu contains Play/Pause, Previous track, Next track, web configuration, current track folder when available, About/version, and Exit.
- `--tray` and `--no-tray` override the saved preference for this run without saving it. `TrayIconEnabled` is stored in the existing global player registry and defaults to enabled. The web configuration has an enable/disable control and shows ownership and override status.
- Normal launches retain the Windows mutex and authenticated IPC handoff. Only the official mutex owner creates the tray icon or executes its commands. `--instance` permits additional playback processes without hijacking the official tray.
- If the official instance exits, a remaining explicit instance may claim the same mutex, publish its IPC endpoint, and create the icon. The claim does not rely on a PID in stale `instance.json`. Normal shutdown removes the icon; Explorer restart attempts to re-add it.
- The single-file release bundles the updated tray, IPC, web workflow, and other companion sources.

## Limits

Windows does not expose a native tray triple-click event. Clicks must remain within each Windows-configured click interval. A sudden process termination may leave a stale shell image until Explorer refreshes it. An additional `--instance` process becomes tray owner only after winning the mutex; other additional processes remain without an icon. A disabled web server cannot be opened from the menu. Visual Explorer-shell verification was unavailable in the automated session, which had no shell window; the native message window and shutdown path were exercised.
