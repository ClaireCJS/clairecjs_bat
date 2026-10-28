# Windows 10 lock-screen status — V530 companion, V611 media bridge

## V611 status

The optional Windows media bridge now asks Windows to select PAFPlayer again
whenever Chrome owns the current media session while PAFPlayer is playing. It
checks at most once every five seconds, whether Chrome reports a paused video
or an active Nest camera. When PAFPlayer is paused, stopped, or no longer the
official instance, it does not contest Chrome's selected card. It never pauses
or controls Chrome playback. Windows still selects the visible right-side card;
there is no supported way for PAFPlayer to guarantee that another app will not
appear there. [Microsoft describes the current session](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssessionmanager.getcurrentsession)
as the one Windows believes the user would most likely want to control.

The detailed-status companion source now requests `🎸 Artist – Song · time`,
`🎤 lyric`, and `💿 Album (Year) – PAFPlayer v611` when version display is on.
The version suffix follows the running player version and survives truncation
of a long album name. This source is tested, but the installed signed V530
companion has not been rebuilt. Its display remains unchanged until a newly
signed package is installed and selected in Windows.

The tray-only client can already relay playback controls to its verified
official server. For **left-side status on a client PC today**, install the
existing signed V530 companion on that PC, open **PAFPlayer Lock Screen** from
Start, enter `http://machineservername:666` as its server, enable publishing,
and save. Select PAFPlayer Lock Screen for detailed status in Windows Lock
Screen settings. The companion accepts a remote hostname and verifies the
official player identity before publishing. Leave its standalone process
running; the tray-only process does not yet manage its lifecycle. The V530
package still uses the old text format until a signed update is installed.

The tray-only process does not yet publish a local **right-side** Windows
media session. Making it manage both surfaces needs a client-side SMTC bridge
whose commands relay to the verified server owner, plus a managed companion
mode for remote hosts. The current managed companion only accepts loopback and
a local player process.

## Right-side media panel (V603)

The existing **Windows / Lock Screen · Experimental** web switch publishes
PAFPlayer's System Media Transport Controls (SMTC) session with title, artist,
album, artwork, playback state, and optional media buttons. Keep that switch
enabled to use the right-side media panel. Its saved off choice and default
off behavior remain respected.

V603 improved how the existing publisher responds when Windows retains a
paused Chrome video as the selected media card. On play start and track
change, PAFPlayer re-registers its session after publishing the new metadata.
When Windows reported Chrome as selected but paused or stopped, PAFPlayer asked
Windows to reconsider after five seconds rather than a minute. V611 extends
that check to active Chrome media while PAFPlayer is playing. If Windows
denies session read-back, it retries at most once every 30 seconds while music
plays. A stopped PAFPlayer track clears its media session.

Only the official/default instance publishes SMTC status or accepts SMTC
playback commands; an explicit `--instance` cannot take ownership. The bridge
runs on the existing workflow thread, away from the audio loop. It is separate
from the optional V530 lock-screen tile/badge package and needs no new package
installation or UAC approval.

Windows chooses the visible media session. Other apps can take focus after
PAFPlayer starts, and Windows may retain a different selected session even
when PAFPlayer publishes correctly. V611's selection behavior is unit-tested;
the exact locked-screen result with an active Nest/Chrome stream still needs a
physical lock-screen check. To check it, start
PAFPlayer music, lock Windows, and inspect the right-side media panel. Then
pause, change tracks, and exit to confirm the status follows or clears. Do
not infer the right-side panel's state from the detailed/quick status tiles:
they are separate Windows surfaces.

V530 carries the next signed companion version inside
`PAFPlayer.py`. Run `PAFPlayer.py --install-lockscreen` to install or upgrade it,
or `--check-lockscreen` for a read-only check. A normal first run attempts setup
once automatically. Certificate trust is never silent: an untrusted development
certificate goes directly to Windows UAC approval during first-run setup. The
explicit install command asks for console confirmation before opening UAC.
When the existing PAFPlayer certificate remains trusted, upgrading V529 to V530
does not require renewed elevation.

V526 rearranges the three detailed-status rows to keep the lyric beside the clock:
**artist – song**, **elapsed/total · current lyric**, and **album (year)**. The
artist/title separator is an en dash. The year is omitted, including its
parentheses, when no Year/Date metadata exists.

V520 adds elapsed/total time and album in the middle detailed-status row, replacing
the previous-lyric row when either field is available. The current lyric stays
on the last row. See the [V520 manual and verification](PAFPlayer_v520_lock_screen_album_and_counter.md).

V519 adds a 250 ms lead to lock-screen lyric selection while playing, scaled by
playback speed. Paused/stopped clocks do not advance. Other lyric displays and audio
keep their existing timing. Windows still controls visible delivery. See the
[V519 measurements and verification](performance-v519.md).

V518 fixed the recurring disappearance caused by V517's independent badge
renewal. It also supplies the previous lyric alongside the current lyric so a
brief cue can remain readable after the next cue arrives. The native Windows
lock screen still controls timing, truncation, font size and clock placement.

## Use lyrics

1. Run the current `PAFPlayer.py` or its versioned release copy. The companion accepts
   older players, but album/counter fields require V520's compact endpoint and the
   250 ms lyric lead requires V519 or newer. Relaunch older players to load them.
2. Keep **Windows Lock Screen → Enable lock-screen song status** enabled.
   Fresh installations remain disabled by default; existing choices are retained.
3. Choose **PAFPlayer Lock Screen V530** in Windows Settings' top **Choose one
   app to show detailed status** slot for text. A bottom quick-status slot shows
   only the playing/paused/idle/offline badge. Both may be selected. The Recovery
   package family and app ID are unchanged, so existing selections should survive.
4. Play a track with timed lyrics. A representative layout is
   `Metallica – One`, `1:15/6:36 · Darkness, Imprisoning Me`, and
   `...And Justice for All (1988)`. Missing lyric or album text uses `♪` so lyric
   gaps still request three nonempty rows.

The counter uses actual playback position, without the lyric lead. It follows
pause, seeks and track changes without extrapolating a separate clock. Duplicate
polls within one displayed second do not cause extra timer updates; lyric changes
still publish immediately on the next poll. Unknown time shows `--:--`, and hours
are supported. Invalid numbers are ignored and elapsed time is capped at a known
duration. Stopping removes the counter; offline status removes album/time entirely.
The counter precedes the lyric so long lyrics cannot truncate it away. Windows may
still truncate any requested row. The quick-status slot only supports preset glyphs
or numbers, so it cannot display a formatted timer or album text.

The current lyric uses the existing timeline plus V519's lock-only 250 ms lead
while playing. Previous context uses that same selected position and lyric offset; it
follows seeks and resets for gaps and new tracks. No speech recognition or second
playback clock is involved. With an older player, the companion retains only the
previous line it actually observed. Long rows are capped at 120 UTF-16 code units
without breaking surrogate pairs, and Windows can truncate them further.

## Cause and delivery fix

The October 9 baseline trace recorded two badge-only renewals followed about
200 ms later by `PublishDetailedStatusChanged` reason 2 with no text update. Text
returned on the next tile update; one absence lasted roughly eight seconds.
This matches the reported disappearing status area and clock movement.

V518 always submits badge then detailed text together whenever content changes
or the unchanged content needs its 30-second renewal. Both share a 90-second
expiration and renewal deadline. It does not clear notifications between lyric
updates. The native Windows trace coalesces arrivals over roughly 200 ms; merely
polling faster cannot guarantee a visible frame for every arbitrarily short cue.
V518/V519 used the extra previous row to retain a preceding cue after a quick
transition, including a cue that fell between polls. V520 uses that row for album
and time when available, so the preceding cue is then not displayed. Multiple rapid
cues can still be missed.

The companion continues polling every 250 ms. PAFPlayer's existing status cadence
is 200 ms, so those stages alone can add about 450 ms, before Windows rendering
and network overhead. This is line-level display, not word-highlighted karaoke.
No notification queue is used to replay stale lyrics. Sleep/suspension can stop
updates. A publisher restart or installation handoff can briefly clear the area.

## Architecture and compatibility

The controller is bundled in PAFPlayer.py and manages the installed signed desktop
publisher in a separate process. Its worker checks ownership/settings every five
seconds; Windows process work is outside the audio callback and visualizer frame.
Disabling the setting or ending the owning player stops managed publication and
clears status; notification expiration is the fallback after abrupt failure.

The compact local GET/HEAD endpoint `/api/remote-tray/hello?lockscreen=1` activates
only the existing status sidecar updates. It copies metadata, transport state,
current and previous lyric text, album and elapsed/total seconds; it does not transfer artwork/full timelines,
activate the browser spectrum, or send playback commands. Previous-cue lookup is
bounded. Ordinary tray requests retain their existing behavior.

The publisher requires `official=true`, a nonempty instance identity,
case-insensitive PAFPlayer program names in root/state, and matching nonempty
versions. Managed mode also pins the launching identity and requires loopback.
Redirects, proxies, cookies and default credentials remain disabled. One reusable
HTTP client has a bounded response size, a three-second timeout, no overlapping
requests, and a three-second backoff after failed reads. Failed reads show offline
status instead of stale track details.

`PAFPlayerLockScreenEnabled`, `PAFPlayerServerUrl`, the Recovery package family,
`!App` identity and existing configuration IDs are preserved. The V530 tile
publisher is separate from the `.scr` screensaver, wallpaper, and the SMTC
media transport panel publisher.
The periodic Windows background task is not a subsecond lyric clock.

## Installation

The currently signed package is
`lockscreen/dist/v530/PAFPlayerLockScreen_v530_x64.msix`, version
`530.0.0.0`. From the PAFPlayer project directory:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py --check
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py
```

The installer verifies pinned hashes, signer, manifest, interactive activation,
publication and background COM activation. It upgrades the Recovery companion;
playback stays running. A successful receipt is not proof of visible pixels.

## V518 verification history

- **148 focused tests passed:** 67 C# and 81 Python, covering paired renewals,
  failed-submission retries, gaps/track changes, short preceding cues, seeks and
  offsets, old-player compatibility, local/official-only reads, browser-inactive
  real HTTP polling, lifecycle, installer and related tray regressions.
- Python compilation, final C# build, full MakeAppx validation, executable/MSIX
  signatures and pinned installer checks passed. Interactive V518 activation,
  tile/badge submission and background COM registration succeeded as
  `DEMONA\Claire`, session 1.
- The real October 9 V518 lock cycle recorded 32 detailed-text updates. One explicit
  clear during the standalone-to-managed handoff briefly removed text; it returned
  about 0.56 seconds later. After the publisher settled, **23 text updates had zero
  reason-2 removals**. This sample supports the recurring-refresh fix, but does not
  visually prove clock stability or delivery of every line.
- Reports: `tests/reports/v518-badge-disappearance-evidence.json`,
  `tests/reports/v518-lock-cycle-analysis.json`, and the linked raw trace names
  inside those reports. The Winlogon trace provider was access-denied; the relevant
  lock-screen text/notification providers recorded successfully. Some other events
  reported schema mismatches during decoding.
- Main-player function/class ASTs match the pre-edit backup. Version constants and
  the bundled lock-screen module changed. The user's intervening edits were kept.
  The historical 678-test V514/V515 comparison had identical 614 passes, 51 failures
  and 13 errors; this narrow release does not claim a clean full-suite result.

## Manual check still needed

After relaunching the player with V520 and allowing the publisher to settle, close
the browser, play a tagged timed-lyric track, and lock Windows manually for a minute.
Confirm artist/song, album, elapsed/total and current lyric are visible. Watch for
clock movement during lyric gaps and rapid cues. Use normal player controls to
check pause/resume, a backward seek, a track from a different album, unknown duration,
and disabling the setting. No stale album/time should survive going offline.
Actual V520 locked-screen appearance and delivery of every cue remain unverified.

## Windows host history and boundaries

The October 8 trace separately recorded Microsoft's LockApp activation failing
with `0x80270252` (`E_UAC_DISABLED`). On October 9 native status was user-confirmed
and a read-only check reported `EnableLUA=1`; this work did not change UAC. That old
failure is not the cause of the now-working screen's V517 refresh regression.
See the [historical investigation](lockscreen-renderer-investigation-20261008.md).

Source/signing replacements have verified backups. Prior releases are preserved.
`play_audio_file.py` and all literal `C:\BAT` paths are unchanged.

## Microsoft references

- [Local tile and badge notifications](https://learn.microsoft.com/en-us/windows/apps/design/shell/tiles-and-notifications/choosing-a-notification-delivery-method)
- [Lock-screen tile and badge presentation](https://learn.microsoft.com/en-us/previous-versions/windows/apps/hh779720(v=win.10))
- [LockScreen API boundary](https://learn.microsoft.com/en-us/uwp/api/windows.applicationmodel.lockscreen?view=winrt-28000)

## V519 validation

See [V519 verification and remaining manual checks](performance-v519.md). The
companion activated and published successfully. The new lyric lead requires the
V519 player; actual timing on the locked screen remains a manual check.

## V520 validation

183 focused checks passed (84 C#, 86 Python integration/installer/tray, 13 renderer).
Compilation, full package validation, signatures, pinned hashes and real interactive
Windows activation/publication passed. The receipt verified the official V518
player, whose compact endpoint lacks album/time; relaunching V520 is required to
visually verify those fields. Main-player function/class ASTs and native encoder
bytes match V519. See the [V520 manual snapshot](PAFPlayer_v520_lock_screen_album_and_counter.md).

- [Microsoft: badge numbers and supported glyphs](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/badges)
