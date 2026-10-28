# PAFPlayer visual screensaver

This is a **separate Windows screensaver application**, not a replacement for
the Windows lock screen. It shows artist — song, the current timed lyric line,
and album artwork. Artwork brightness is adjustable without dimming the text.
It is disabled by default.

## Architecture and Windows limitations

`PAFPlayer.scr` is a compiled x64 .NET Framework WinForms GUI executable. It
does not import Python, start a decoder, open an audio device, or control audio.
Windows invokes `/s` for fullscreen, `/p HWND` for its preview pane, and `/c`
for the native settings window. No arguments behave like `/c`. Both `/p:HWND`
and `/p HWND` are supported; `/port:NNNN` selects a different local player port.
Microsoft's [screensaver sample](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms686421(v=vs.85))
documents the executable/argument contract.

The fullscreen display shows artwork and lyrics on the **primary monitor** and
covers every other monitor with a borderless black window. Negative monitor
coordinates, mixed DPI, and display-layout changes are handled together.
After a three-second grace period measured from first display, dismissal
requires a one-second key or mouse-button hold, two key hits within two
seconds, or two seconds of sustained pointer motion. Startup input is discarded.
An initially disabled player shows an explanation instead of closing the saver.
All black windows close together with the main display. Preview is a
real child window, does not grab the keyboard or hide the pointer, follows its
parent's size, and exits when the parent closes. A local mutex prevents duplicate
fullscreen instances for the same session/port. The content shifts slightly at
20-second intervals; this is not a guarantee against OLED burn-in.

Windows owns screensaver idle activation. The native Settings window has a
per-machine **Require password after lock** option. When selected, a normal
fullscreen exit requests a Windows workstation lock, including exits requested
by PAFPlayer's Close button. Windows may show the lock screen before the sign-in
field. The option starts off and does not change the system-wide screensaver
security policy. Preview mode never locks the workstation.
Secure screensavers and the protected Winlogon desktop are distinct from an
ordinary application's fullscreen window. Window messages cannot cross desktop
boundaries; ordinary applications do not have unrestricted access to Winlogon.
See Microsoft's [desktop security model](https://learn.microsoft.com/en-us/windows/win32/winstation/desktops).
This feature does not modify lock-screen wallpaper, change the selected system
screensaver, or register a service on the secure desktop. Windows' documented
`LockWorkStation` request is asynchronous and may fail if the process cannot
access the interactive desktop. A forced process termination cannot run the
normal exit lock path.
Group Policy may override Windows' selected screensaver; selection changes apply
to later launches, as documented for [SCRNSAVE.EXE](https://learn.microsoft.com/en-us/windows/win32/devnotes/scrnsave-exe).

The existing Windows media/SMTC integration remains separate and keeps its
configuration keys. Windows decides how that media card appears. It is not the
arbitrary artwork-and-lyrics window implemented here.

### Data flow

```text
Existing player status + cached primary cover
    ↓ small loopback-only HTTP endpoints, no image conversion
PAFPlayer.scr background reader, below normal priority
    ↓ one latest-state mailbox and at most one pending decoded image
WinForms UI: artwork, artist — song, current lyric
```

- `GET /api/screensaver/state` returns protocol version, player version, session,
  enable state, brightness, display text, status and artwork revision. It does
  not return paths, pairing secrets, full metadata, spectrum or the lyric list.
- `GET /api/screensaver/art?revision=…` serves the existing primary cover bytes.
  A track/artwork generation mismatch returns 404 rather than the wrong cover.
- `POST /api/screensaver/settings`, `/show`, and `/close` use the existing
  local workflow pairing token and same-origin validation. Reads and writes are
  loopback-only even if other web features permit remote clients.
- Persistent settings use a new `visual_screensaver` object with `enabled`
  (default false) and `brightness` (0–100, default 50). The existing workflow
  settings writer verifies a replacement backup. No existing configuration ID,
  Windows media option, or favorite/default selector is renumbered or repurposed.
- A separate activity signal keeps the existing status/lyric publisher awake
  at its normal rate while the sidecar is reading. It does not enable browser
  spectrum work. The activity signal expires three seconds after polling stops.

### Resource and failure behavior

The sidecar has one background reader, with at most five completed status polls
per second, and retries an unavailable player once per second. Requests use
timeouts, loopback-only URLs, no proxy, no redirects, and response-size limits.
Art downloads occur only on revision changes; transient fetch failures back off.
Successfully fetched corrupt or unsupported art is not repeatedly downloaded.

Compressed art is capped at 16 MiB, decoded source dimensions at 32 million
pixels, and the retained display bitmap at 1024 pixels per side. GDI+ supports
the usual JPEG/PNG/GIF/BMP covers; unsupported formats such as WebP may show text
without artwork. Image decoding, scaling and brightness rendering happen in
the sidecar process. The server does not transcode covers. Replaced images,
graphics objects and timers are disposed, and a stalled GUI cannot accumulate
a queue of old frames.

Stopping or crashing the sidecar does not send a playback command. A missing or
unreachable player clears stale song/lyric/artwork and shows a waiting view.
An available player with the feature disabled is identified explicitly in the
preview; fullscreen exits when disabled. **Close screensaver** also reaches an
instance launched by Windows through a session-scoped close revision. Player
restart creates a new session and the sidecar reconnects. The primary desktop's
HTTP endpoint can be used without cross-desktop window messaging, but secure
idle activation still needs testing on the actual Windows installation.

## Project layout and building

The working project is `C:\codex\clairevironment\bat\PAFPlayer`. `C:\sandbox`
is currently a junction to `C:\codex\clairevironment\bat`, so the same directory
is `C:\sandbox\PAFPlayer`.

- `PAFPlayer.py`: current single-file player, including the embedded bridge.
- `tests`: shared Python regression tests; `tests\runs` retains isolated results.
- `releases`: descriptive version snapshots and release records.
- `screensaver`: runtime `.scr`/configuration and build sources.
- `screensaver/docs`: documentation.
- `screensaver/releases`: backups and previous releases.
- `screensaver/testing`: active tests and verification tools.
- `screensaver/testing/old`: completed test artifacts and historical diagnostics.
The current player is `PAFPlayer.py`; historical `play_audio_file.py`
references in older release records refer to its predecessor.

From the repository root:

```powershell
C:\ProgramData\anaconda3\python.exe -B -X utf8 PAFPlayer\screensaver\tools\build_PAFPlayer_screensaver.py
C:\ProgramData\anaconda3\python.exe -B -X utf8 PAFPlayer\screensaver\testing\verify.py
C:\ProgramData\anaconda3\python.exe -B -X utf8 PAFPlayer\tests\run_PAFPlayer_tests.py
```

Building requires the installed .NET Framework 4 x64 C# compiler; no NuGet,
PyInstaller, network download or Python environment is needed to run the `.scr`.
Close the screensaver and Windows preview before rebuilding its installed file.
The verification command builds a separate executable in a new test directory,
so it can test without replacing an open preview. Tests use synthetic audio/data
and hidden preview hosts; they do not play music or change live settings.

When launched by PAFPlayer, the bridge prefers `screensaver\PAFPlayer.scr`
inside this project, then a sibling `.scr`, then `C:\BAT\PAFPlayer.scr`.
The `/port` argument follows the player's actual port. Windows automatic launch
uses port 666 by default; use that player port for idle activation in this version.
The player HTTP server must be enabled.

## Native settings and hold-to-preview

Windows **Settings…**, right-click **Configure**, or `PAFPlayer.scr /c` opens
actual controls for enabling the screensaver, setting artwork brightness, and
requiring Windows sign-in after normal fullscreen dismissal. The window is
760 × 520 client pixels, with scrolling space for high DPI layouts.
Apply saves; OK saves and closes; Cancel discards unsubmitted changes. These
use the same authenticated loopback API and persistent settings as the web UI.
The password choice is saved in this machine's `PAFPlayer.cfg` and works even
when PAFPlayer is not running. Enabling and brightness also sync to the player
when it is available; sync failures remain visible and can be retried. No
browser is required.

After the initial three-second startup grace, a single key press or click does
not close the fullscreen saver. Hold a key or mouse button for one second,
press two keys (including two separate presses of the same key) within two
seconds, or move the pointer continuously for two seconds. Mouse jitter and
brief motion pauses do not count. This timing applies to all monitors.

Hold the left mouse button on **Hold to preview** for a fullscreen preview:
artwork/lyrics on the primary monitor and black on every other monitor. Release
anywhere to close it immediately, without the normal three-second grace period.
Losing capture, switching windows, or closing Settings also clears the preview.
It uses unsaved brightness locally and never writes settings simply to preview.
When no live enabled song is available, a sample demonstrates the appearance.

## Updating and selecting the screensaver

Right-click **Install** invokes `rundll32.exe desk.cpl,InstallScreenSaver` for
that `.scr` path, selects it in Windows Screen Saver Settings, and opens the
settings dialog. Apply/OK retains the selection. This is a path registration,
not a separate installed copy. Replacing that exact file updates future launches;
there is no need to install it again. If you move it or select a different copy,
install/select the new path once. Close an open saver/preview before replacement.
`screensaver/src/PAFPlayer_screensaver.cs` is the editable source;
`screensaver/PAFPlayer.scr` is the executable Windows launches.

The September 29 startup hotfix adds the three-second input grace period,
keeps an initially disabled saver open with instructions, and displays the local
endpoint and failure reason while retrying a failed connection. It needs no
player restart. The existing live V474 feed was verified separately with the
native reader (title, current lyric, and decoded cover).

## Manual verification

1. Run the current `PAFPlayer.py` and open its local web controls. Find **Visual
   Screensaver**, distinct from **Windows / Lock Screen**. Confirm it starts off.
   Start the `.scr` with `/p` through Windows Screen Saver Settings: the preview
   should say **PAFPlayer detected — screensaver disabled**, not that the player
   is missing. For the observed V473 session on port 666, the player was detected
   and the feature was disabled; enabling the separate checkbox is required.
2. Enable **Visual Screensaver**, then click **Show screensaver**. Play a tagged
   track with a timed `.lrc` or `.srt` and a JPEG/PNG cover. Confirm artist/title,
   cover and the current lyric, including accented characters and long lines.
   Use a missing-art/missing-lyrics track and confirm there is no previous cover
   or leftover lyric.
3. Pause, resume, seek and advance normally. Compare the displayed line with the
   player's other lyric displays; normal status resolution is about 200 ms, not
   word-by-word karaoke animation. Confirm the final audio seconds still play.
4. Change brightness to 0, 50 and 100. Only the cover should dim. Restart the
   player and confirm the setting persists. Existing SMTC and favorite/default
   values should remain unchanged.
5. Close with a one-second hold, two key hits, or sustained pointer motion. Show
   again, then use **Close screensaver**. With the password option enabled, both
   normal exits should request the Windows lock screen and sign-in.
   Show again, then disable the feature. Confirm music continues through each.
   Re-enabling permits showing it; it does not automatically take over the screen.
6. Close the player while the sidecar is open. Confirm the waiting view clears
   old lyrics/artwork, then restart the player and check reconnection. Launching
   with an incorrect `/port` should wait without a crash or busy loop.
7. Run `PAFPlayer.scr /c`, edit brightness, verify hold/release Preview, then
   Apply/Cancel behavior and synchronization with the web settings. In Windows Screen
   Saver Settings, select the sidecar explicitly if desired, test its preview,
   resize/close the dialog, then test real idle activation. Windows' sign-in-on-
   resume and organizational policy remain Windows settings. Verify those
   separately; a successful manual `/s` display proves no lock-screen integration.
8. With console, artwork popup and floating lyrics also active, observe playback
   and FPS, then leave the sidecar running across many track/cover changes.
   Check process private bytes and GDI handles for a stable working range.
   Repeat on the actual display scaling setup. Automated checks do not replace
   this long-session and secure-desktop verification.

The automated verification report records actual results. It does not assert
that the complete historical player suite is green or that Windows secure
activation and hours of live playback have been manually verified.
