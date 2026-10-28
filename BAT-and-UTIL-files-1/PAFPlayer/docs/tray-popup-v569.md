# Tray popup API isolation — V569

## Cause

The wallpaper worker used `ctypes.windll.user32.SystemParametersInfoW` and
set its third argument to `LPWSTR` for a wallpaper filename. The lyric bubble
and full-info hover card reused that cached function for `SPI_GETWORKAREA`,
which takes a pointer to a `RECT`. A wallpaper read followed by the work-area
query reproduced the exact reported `argument 3: TypeError: wrong type` on
this Windows computer. This can persist after turning album wallpaper off,
because the shared function's declared types remain changed in the process.

The tray timer attempted the same paused lyric repeatedly. Because the exception
occurred before recording that lyric as handled, each timer sync threw out of
the Windows callback again. MonkeyMote lyrics were unrelated to this failure.

[Python's ctypes documentation](https://docs.python.org/3/library/ctypes.html)
explains that function attribute access returns a cached wrapper, whereas
indexed lookup returns a fresh wrapper. Microsoft's
[SystemParametersInfoW contract](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfow)
requires a RECT pointer for SPI_GETWORKAREA and a text buffer for
SPI_GETDESKWALLPAPER.

## Fix and compatibility

- Give both popup classes a private, cached set of typed Windows API wrappers.
  Work-area queries use a void pointer appropriate to the Windows contract.
  Wallpaper reads/writes use their own function wrappers.
- Use pointer-sized handle results and arguments for window and drawing APIs,
  and the same PAINTSTRUCT type for both popup painters. These prevent related
  ctypes collisions when full-info and lyric popups alternate.
- Destroy popup windows, release fonts and brushes, and unregister their window
  classes on close. Recreating popups in the same process is tested.
- Record each attempted lyric before showing it and contain native exceptions.
  A failed identical paused line does not repeatedly throw/log. A new line or
  toggling the lyric option off and on allows another attempt.

Settings IDs, popup placement, appearance, click-through behavior and hover
delay are preserved. External tray modules and the single-file player's
embedded copies match. Playback, lyric timing, MonkeyMote protocol, lock-screen
publishing and play_audio_file.py are unchanged. No literal C:\BAT path changed.

## Automated verification

Run from the PAFPlayer directory:

```powershell
C:\ProgramData\anaconda3\python.exe -B -X utf8 tests\verify_v569_tray.py
```

116 tests passed, with no failures, errors or skips. They cover the reported
native signature conflict, successful work-area reads under that conflict,
wallpaper wrapper isolation, paused retry behavior, native popup create/show/
paint/hide/close, existing tray behavior, track details, wallpaper handling,
MonkeyMote multi-client/protocol tests, remote controls and selected queue/web
regressions. The native test performs four complete two-window cycles and
96 explicit paint dispatches, verifies visibility/hiding and destroyed HWNDs,
and checks stable GDI/USER counts after the initial Windows drawing warmup.
The wallpaper setter is mocked; tests do not change the desktop wallpaper.

The first test run exposed an outdated track-details fake runtime missing its
app settings interface and first-paint Windows resource initialization. The
fixture now provides that interface without changing its assertions; the
resource check now warms both painters before checking each subsequent cycle.
Both original and corrected reports are retained.

This is focused verification, not a claim that all historical 600+ tests pass.
Tests use preserved isolated staging, block live configuration/log writes and
non-loopback connections, and do not send playback commands to the running
player. Reports are in tests/reports; test copies remain in tests/runs.

Evidence: [baseline reproduction](../tests/reports/tray-v569-baseline-20261016.json),
[116-test results](../tests/reports/tray-v569-checks-20261016-221649.json), and
[test log](../tests/reports/tray-v569-checks-20261016-221649.log).

## Full-player manual check

1. Restart the usual official player using the updated PAFPlayer.py (V569).
   Existing processes retain V568's embedded code until restarted.
2. Enable album artwork as desktop wallpaper and sung lyrics above the tray.
   Play a song with lyrics, then pause it for at least 30 seconds. Confirm the
   lyric bubble stays usable and no repeated ctypes callback tracebacks appear.
3. Enable Full info on tooltip and hover over the tray icon. Confirm artwork
   and metadata display while the lyric bubble also works. Move away and check
   that the card hides; toggle the lyric option off and on.
4. Resume, change tracks and verify normal tray controls and MonkeyMote clients.

Real Windows API execution passed in the automated test, but the full player's
visual behavior after the user's restart has not yet been verified. No running
player was restarted or altered during the test.
