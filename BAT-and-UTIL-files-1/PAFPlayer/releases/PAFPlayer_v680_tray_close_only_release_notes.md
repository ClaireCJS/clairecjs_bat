# PAFPlayer V680 — tray-only close and full shutdown

## Change

The official Windows tray menu now exposes two distinct actions:

- **Close PAFPlayer tray (only)** removes the notification-area icon and tray-owned windows without stopping playback.
- **Shut PAFPlayer down completely** retains the existing full shutdown behavior and stops the player/music process.

The distinction is implemented in `TrayController.dispatch()`: tray-only
closure calls the controller's local `close()` method, while full shutdown is
the only action that calls `server.enqueue_tray_exit()`.

## Verification

- `PAFPlayer.py` compiles successfully.
- Embedded `PlayWaveFileTests.test_v680_tray_close_only_is_separate_from_full_shutdown` covers menu labels, action mapping, and the no-playback-exit guarantee.
- The bundled `PAFPlayer_tray` source matches `src/PAFPlayer_tray.py`.

## Files

- `PAFPlayer.py` — V680 active single-file player.
- `src/PAFPlayer_tray.py` — editable tray implementation.
- `docs/windows-tray.md` — tray behavior documentation.
