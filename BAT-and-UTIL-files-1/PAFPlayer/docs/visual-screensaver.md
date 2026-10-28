# Visual screensaver exit and sign-in

V507 makes the native `PAFPlayer.scr /c` settings window wider and taller and
adds **Require password after lock**. The checkbox is saved per machine in
`screensaver/PAFPlayer.cfg`, defaults off, and can be changed without a running
player. When selected, closing a shown fullscreen screensaver normally requests
the Windows workstation lock. This includes closing it through PAFPlayer's
**Close screensaver** control. Windows controls the lock and sign-in screens;
it may show the lock-screen image before the password field.

After the existing three-second startup grace, one keypress or mouse click no
longer ends the screensaver. Hold a key or mouse button for at least one second,
press two keys within two seconds, or keep the pointer moving for two seconds.
Pointer jitter and pauses do not count. This applies across the primary and
secondary monitors. **Hold to preview** in Settings still ends immediately when
released and never locks Windows.

The player requests a normal sidecar exit when **Close screensaver** is used, so
the optional lock path can run. An abnormal process termination cannot run this
path. Windows' [`LockWorkStation`](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-lockworkstation)
request is asynchronous; its return value cannot guarantee that the workstation
locked. See the [screensaver guide](../screensaver/docs/README.md) for setup and
test steps.
