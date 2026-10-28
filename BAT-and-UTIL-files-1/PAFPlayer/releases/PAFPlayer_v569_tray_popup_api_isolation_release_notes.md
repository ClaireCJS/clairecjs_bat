# PAFPlayer V569 — tray popup API isolation

Fixes the repeated `ctypes.ArgumentError: argument 3: TypeError: wrong type`
from the tray lyric bubble while playback is paused.

The wallpaper worker changed the argument signature of a cached Windows API
function to accept a string. Popup placement called the same function with a
rectangle. V569 isolates the bindings, types native handles correctly, shares
the paint structure between both popup types, and releases popup window classes.
A failed lyric display attempt is contained and is not retried every timer tick
for the same paused line. New lyrics or toggling the option permits a retry.

The single-file PAFPlayer.py and the three external tray modules are synchronized.
Main-player executable code outside those modules and the version/build constants
is identical to V568 by AST comparison. All other 18 embedded modules, including
MonkeyMote, are unchanged. Existing settings IDs remain compatible.

## Verification

- 116 focused and related regression tests passed; zero failures, errors or skips.
- Reproduced the exact old error on this Windows computer before fixing it.
- Real Windows popup creation, visibility, 96 explicit paint dispatches, hiding,
  destruction and repeat creation passed under the conflicting legacy signature.
  No callback exceptions; stable GDI/USER counts after initial Windows warmup.
- Main source, all 21 embedded Python modules, external changed modules and tests
  compiled successfully. Release copy SHA-256 matches PAFPlayer.py.
- An old track-details test fixture was updated to provide the existing runtime
  app/settings interface; its assertions were preserved.
- Your V568 feedback confirms two simultaneous real MonkeyMote clients connected
  and lyrics work. The second device platform was not specified. Android-specific
  behavior, physical live-port edits and long-duration use remain unverified.
- These are focused tests, not a new full historical-suite run. The test harness
  blocked live settings/log writes and non-loopback networking. Actual wallpaper
  changes were mocked and no playback commands were sent to the running player.

Restart your usual PAFPlayer using PAFPlayer.py to load V569. Running V568 cannot
load corrected embedded modules automatically. Full-player visual verification
following restart remains outstanding; see [manual procedure](../docs/tray-popup-v569.md).

[Detailed test log](../tests/reports/tray-v569-checks-20261016-221649.log),
[compilation and scope check](../tests/reports/tray-v569-compilation-20261016.json),
and [complete affected-path inventory](../tests/reports/tray-v569-change-inventory-20261016.md).

Existing release artifacts were not overwritten. Required replacement backups
were created and SHA-256 verified. No pre-existing files were deleted or moved.
No literal C:\BAT paths changed. play_audio_file.py was not modified.
