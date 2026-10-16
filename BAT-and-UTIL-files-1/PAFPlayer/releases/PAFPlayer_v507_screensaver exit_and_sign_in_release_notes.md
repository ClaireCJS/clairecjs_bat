# PAFPlayer V507 — Screensaver exit and sign-in

- Enlarged the native screensaver settings window to a 760 × 520 client area, with a 640 × 440 minimum and a scrollable body.
- Added **Require password after lock**, saved per machine in `screensaver/PAFPlayer.cfg`. It defaults off. A normal exit from a shown fullscreen screensaver requests `LockWorkStation`; preview and the settings window do not lock Windows.
- Retained the three-second startup grace. After it, dismissal requires a key or mouse button held for one second, two key hits within two seconds, or sustained pointer movement for two seconds. Key auto-repeat, a single click, pointer jitter, and short movement bursts do not count.
- Changed the player's **Close screensaver** action to request a normal sidecar exit. This lets the optional lock action run instead of terminating the sidecar first.
- Synchronized the single-file player's bundled screensaver bridge with the standalone bridge source.

Windows controls the lock and sign-in screens; the lock screen may appear before the password field. `LockWorkStation` starts an asynchronous request, so the app cannot guarantee that Windows completed the lock. Forced process termination cannot run the normal exit path.
