# PAFPlayer V509 — lock-screen activation diagnostics

V509 changes the Windows 10 lock-screen companion from a Debug MSIX to a signed Release x64 MSIX. The Release build uses the .NET Native framework/runtime and release VCLibs dependencies. The package and dependencies are included in the V509 portable installer bundle; the V505 Debug package and dependencies have been moved into `lockscreen/archive/`. The V505 release copy remains intact.

The installer verifies package and dependency hashes, checks its signature, and updates an older installed version. It now checks Windows `EnableLUA`. When systemwide UAC is disabled, it reports the condition and exits instead of treating package registration as proof that the app opens. It never changes this security policy or restarts Windows.

On the Windows 10 test computer, V509 compiled, signed, verified and registered successfully. Its three dependencies have `Status=Ok`. Clicking Start still produced Windows activation error `0x80270254` during the deployment phase before the app process started. The same error occurred with V505. The computer has `EnableLUA=0`; whether restoring UAC and rebooting resolves this remains unverified. The companion window and lock-screen detailed-status picker must be visually checked after that system change.

The existing detailed-status behavior is unchanged: the companion reads the official PAFPlayer instance over the configured LAN endpoint, writes title/artist/state and current lyric to a Windows tile, and requests a 15-minute background refresh. Windows controls actual scheduling and lock-screen display. This is separate from the tray and screensaver.

Verification: Release x64 MSBuild completed, SignTool signed and verified the MSIX, Windows registered V509 and its three dependencies, and the focused package/installer tests and Python compilation checks passed. See `docs/windows-lock-screen.md` and `lockscreen/README.md` for setup and the remaining activation limitation.
