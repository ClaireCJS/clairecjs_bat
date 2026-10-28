# V516 native lock-screen display investigation — 2026-10-08

**Historical October 8 capture.** On October 9 the user confirmed native status
is now visible. A subsequent read-only check reports EnableLUA=1. The agent did
not change that setting. The rejection documented below describes the captured
October 8 session, not the current working lock screen. V517 adds timely lyric
updates; see [current behavior and verification](windows-lock-screen.md).
No product release or installed package was replaced during the October 8
investigation itself.

## Confirmed cause from the completed 18:34 lock cycle

The October 8 capture `tests/reports/lock-renderer-20261008183431-c976e5`
records the actual Windows rejection. Times below are local EDT:

1. At 18:34:58.648, `Microsoft.Windows.LogonController` attempts
   `Microsoft.LockApp_cw5n1h2txyewy!WindowsDefaultLockScreen`.
2. At 18:34:58.934, `Microsoft.Windows.Shell.LockAppHost` records
   **`AttemptingToActivateLockAppWhileElevated`**, with `hr=-2144927150`.
   As an unsigned HRESULT this is **`0x80270252`, `E_UAC_DISABLED`**.
   Both the installed Windows SDK header and Windows FormatMessage identify it
   as an app activation rejection because UAC is disabled. The event's host
   PID 227472 was subsequently identified as Explorer.
3. Shell error `0x80270001` propagates through the controller. Windows then
   records `BeginSecureLock` and a successful `LockOnDesktop` with
   `onSecureDesktop=1`, `hr=0`, at 18:34:58.943.
4. WTS confirms the locked session at 18:34:59.758 and unlock at 18:35:34.928.
   Observations show LogonUI, no LockApp process, and PAFPlayer's publisher
   PID 262036 throughout. The observer stops successfully at 18:35:40.028.

This resolves the earlier hypothesis below: the rejection is now observed,
not inferred from EnableLUA alone. Windows falls back from its app-based lock
screen to the secure LogonUI display. The user may still see a clock/date
surface; that does not establish that LockApp successfully activated.
Calculator's working UWP activation and the working PAFPlayer desktop publisher
do not contradict this specific Windows lock-host failure.

The ETL was decoded using `tracerpt` to preserve self-describing TraceLogging
metadata. `Get-WinEvent` alone did not decode those provider/event names.
The `-decoded.xml` and compact `-conclusion.json` report retain the exact event
sequence, source hashes and WTS observations. The JSON was checked for the exact
HRESULT, successful secure-lock transition, publisher continuity and clean stop.
Do not interpret the secondary `0x80270001` as a NAP/network failure merely
because FormatMessage finds that numeric value in another facility's messages.

### Supported API boundary

Microsoft's [Windows SDK error definition](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/shared/winerror.h)
defines `E_UAC_DISABLED` as `0x80270252`. Its
[lock-screen overview](https://learn.microsoft.com/en-us/previous-versions/windows/apps/hh779720(v=win.10))
explains that Windows mirrors tile text and badges into the selected slots.
The [LockScreen API documentation](https://learn.microsoft.com/en-us/uwp/api/windows.applicationmodel.lockscreen?view=winrt-28000)
states that third-party developers cannot create a replacement lock screen.

PAFPlayer can own and update its registered notification identity; it cannot
use these APIs to replace the rejected Windows renderer or draw its status
slots into the fallback LogonUI surface. No supported workaround has been
established that preserves this computer's current session and disabled-UAC
configuration. This conclusion concerns the selected native status slots on
this machine, not every UWP application or all possible Windows configurations.
A screensaver, desktop overlay, wallpaper update or media-control panel would
be a different feature and is not claimed as a fix.

No UAC change, reboot, shell replacement, package reinstall or further lock
cycle is warranted by this diagnosis. UAC and playback remain unchanged.
Visible native text/badge acceptance still fails; the investigation established
the platform blocker rather than producing a new rendering fix. V516 remains
the software release; immutable release files were not rewritten.

## Confirmed evidence

- The live official server identifies itself as V516, program `PAFplayer`.
- Its managed publisher runs in the interactive Windows account's session 1.
- Windows accepts tile and badge updates every five seconds for
  `ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2!App`.
- A read-only notification-store inspection found current song/artist text and
  `<badge value="playing"/>`, with current expiration times.
- The same handler has `s:tile=1`, `s:badge=1`, `s:lock:tile=0`, and
  `s:lock:badge=0`. These undocumented store values are evidence to investigate,
  not a supported configuration API. Do not write to this database.
- The logged-on user and publisher account match. Windows is Windows 10 Pro
  22H2, build 19045.7663. EnableLUA remains 0.
- No LockApp Image File Execution Options override or matching lock-screen
  bypass scheduled task was found. The existing NoLockScreen policy is 0.
- The current package has the lock-screen visual declaration and a registered
  COM background task. It does not declare the legacy `windows.backgroundTasks`
  extension. Whether this distinction affects this machine's lock-screen
  admission remains unproven; do not label it the root cause yet.
- The global lock-screen toast preference is disabled. This does not by itself
  establish why tile/badge status is absent. No privacy preference was changed.

## What the traces actually establish

`tests/reports/lock-renderer-20261008135614-3247ce.jsonl` recorded no WTS lock
transition in its 15-minute window. Its ETL contains publisher notifications,
but no observed renderer lock cycle. That is inconclusive about locked behavior.
The early two captures failed to start ETW and are retained as diagnostics.

A fresh observer was started at 17:37:26 local time, with report prefix
`tests/reports/lock-renderer-20261008173726-5f560f`. It stops automatically after
the first observed lock/unlock cycle plus five seconds, or after 15 minutes.
The correctly named `Microsoft-Windows-Immersive-Shell` provider was added live;
`Microsoft-Windows-TWinUI` is a channel name, not the provider name.

Settings UI inspection failed: accessibility returned null, screenshot capture
reported `FrameArrived timed out`, and a fresh-window retry reported
`window capture timed out`. No Settings selection was changed through automation.

## Reproduce without changing playback or Windows settings

### Confirmed lock cycle at 17:43–17:44

The user completed the requested test. WTS recorded locked session 1 at
17:43:40 and unlocked at 17:44:39. `LogonUI.exe` PID 59292 appeared while
locked; `LockApp.exe` never appeared in the one-second process observations.
The PAFPlayer publisher PID 262036 remained present. The capture ended cleanly
at 17:44:45, with `saw_lock=true` and trace stop code 0.

The ETL contains 36 Winlogon events, 2544 Immersive-Shell events, and 943
notification-platform events. No LockApp activation appears in the recorded
Immersive-Shell events and no lock-screen content/data provider events were
captured. This narrows the failure to the missing Windows lock-screen host;
it does not yet prove which activation condition caused the bypass.

`SessionData\AllowLockScreen=1`, `NoLockScreen=0`, and Winlogon `DisableCAD=1`
were read without modification. Calculator's actual installed manifest is UWP
(`EntryPoint="Calculator.App"`), and its process exists. Do not mislabel
Calculator as a desktop app or claim all UWP activation is broken.

Read-only token inspection found Explorer and the publisher at high integrity
(`0x3000`); Calculator is at low integrity (`0x1000`). Installed Microsoft host
binaries contain an `AttemptingToActivateLockAppWhileElevated` diagnostic event.
This is a hypothesis to test, **not yet an observed rejection event**.

A further bounded trace started at 17:47:30, prefix
`tests/reports/lock-renderer-20261008174730-0d8ac0`. In addition to prior providers,
it enables the installed binaries' TraceLogging providers LockScreenController,
LockAppHost, LogonController, and LockScreenExperienceManager. The user was asked
for another 20-second lock cycle. It expires automatically by 18:02:30 if no
cycle occurs. No Windows setting or process token was modified.

Run under the interactive Windows account in an elevated shell if ETW requires it:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\observe_lock_renderer.py
```

Wait for `etl_started: true`. The user then presses Windows+L, leaves the
clock/date wallpaper visible for 20 seconds, unlocks manually, and reports what
was displayed. The observer never locks or unlocks Windows, sends no playback
commands, takes no secure-desktop screenshots, and changes no notification,
privacy, UAC, package, or selection settings. Reports use unique names directly
under `tests/reports`; the trace is bounded to 32 MB and 15 minutes.

Use the WTS lock flag and LockApp/LogonUI process observations together with
notification presentation-session and Immersive-Shell activation events to
distinguish a missing renderer from rejection of this app's status. If the user
is viewing a screensaver, monitor sleep, or the password/PIN screen, distinguish
that from the native clock/date lock-screen surface before changing code.

## Long wait for the next manual lock cycle

The 17:47 capture expired without a lock cycle before the user saw the request.
Use this option to avoid another short appointment window:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\observe_lock_renderer.py --wait-hours 24
```

It waits up to 24 hours and automatically stops five seconds after the first
observed lock/unlock cycle. The user can lock for 20 seconds at a convenient
time, unlock manually, then report “done.” ETW stays in a 32 MB circular buffer
while waiting, preserving activation events that precede the WTS locked flag.
While unlocked, the observer polls only the small WTS state query once a second;
it enumerates processes initially, on state changes, and while locked.
The default without this option remains 15 minutes. No player restart is needed.

## References

- [WTS session lock-state flags](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/ns-wtsapi32-wtsinfoex_level1_w)
- [Lock-screen manifest requirements](https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-uap-lockscreen)
- [Microsoft lock-screen sample](https://learn.microsoft.com/en-us/samples/microsoft/windows-universal-samples/lockscreenapps/)

No literal `C:\BAT` path was created, modified, deleted, renamed, or replaced.
