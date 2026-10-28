# Remote Floating Lyrics — V574

These fixes are also retained in the V575 working source. The V574 release copy
preserves the exact source used for the tests below.

## Why the remote lyrics strobed

The remote overlay polls playback position every 50 milliseconds. It also sent
an unchanged track-identity event on every poll. Each event made the renderer
show the artist/song intro and schedule another hide timer. The intro repeatedly
overwrote the sung line, and old timers could withdraw the window. Delayed GUI
work could also accumulate visibility toggles.

The client now sends track identity only when the owner, track path, artist or
title changes. Playback clocks still update frequently. Visibility uses one
absolute enabled/disabled request per change, including startup with lyrics
already enabled. Real cues and new tracks cancel the previous intro-expiry timer.
Existing lyrics mode IDs, preferences and normal local toggle controls remain
compatible.

The separate artwork and lyric Tk interpreters now have explicitly owned control
variables. Shutdown waits for the lyric renderer before releasing the artwork
interpreter's closure cycles. The tray's DestroyIcon binding uses a native HICON
argument, avoiding the observed handle-overflow exception.

## Whip Emojimaxx

The substitution remains `𓀓𓀝` (U+13013 and U+1301D). The installed Segoe UI,
Segoe UI Emoji and Segoe UI Symbol fonts lack these glyphs; Segoe UI Historic
contains both. The renderer checks unsupported ordinary-text runs as well as
emoji runs and falls back to Segoe UI Historic when appropriate. Font/coverage
lookups are cached, and joined emoji sequences stay together.

The client needs its usual Pillow/fontTools support and a font containing the
characters. This Windows test used `C:\Windows\Fonts\seguihis.ttf`. No fonts
were installed or replaced. If the fallback font is absent, available fonts
remain in use; a missing glyph is still possible.

## Port 666 is configurable

The existing `--web-port=PORT` changes the web/remote-tray HTTP port for that run;
666 remains the default. Give the client the same port. In separate prompts:

```powershell
python PAFPlayer.py --no-tray --web-port=7777 "C:\Music\song.flac"
python PAFPlayer.py --tray-only 127.0.0.1:7777
```

Use an existing audio file. Do not use `--instance`: the official player must
own the server. If a normal player is already running, stop it yourself before
this manual test; normal launches reuse the official instance.

For another computer, bind `--web-host` to the player's actual home-network
address and use that address on the client, for example:

```powershell
python PAFPlayer.py --no-tray --web-host=192.168.0.17 --web-port=7777 "C:\Music\song.flac"
python PAFPlayer.py --tray-only 192.168.0.17:7777
```

The HTTP interface is intended for a trusted private network. This work changed
no firewall/network policy. MonkeyMote's separate port (normally 19371) is
unaffected.

## Verification completed

- `tests/verify_v574_remote.py`: **143 tests passed**, no failures/errors/skips.
  Coverage includes track/visibility transitions, delayed GUI work, restored
  enable state, reconnect, paused/stopped clocks, actual Windows glyph masks,
  V573 character recovery, floating positioning/title preferences, tray owner
  routing, MonkeyMote and web workflow regressions.
- In-memory Python compilation passed for the player, all **21 embedded
  modules**, the modified external modules and three new test tools. External
  and embedded module equality was verified. Compilation and structural
  comparison confirmed V575 retains the exact lyric renderer fixes.
- `tests/probe_remote_floating.py` launches an actual isolated silent player
  with `--no-tray` and a separate real `--tray-only` client over loopback using
  a non-default HTTP port, synthetic timed lyrics, rainbow and Emojimaxx. The
  observer records actual Tk window state and renderer events.
- Baseline: **38 of 169** sampled states were withdrawn, with repeated title
  replacement. Final runs: **72/72** and **73/73** normal (visible) states. Both
  processes exited with code zero in each run, no recorded callback/unraisable
  errors, and empty client error logs. One began with lyrics mode off; the
  second restored saved mode 2 (Both).
- Test profiles, media, logs and copied sources are isolated under tests. The
  user's active player was not stopped or sent playback commands.

Evidence: [143-test report](../tests/reports/remote-v574-checks-20261018-124206.json),
[normal-start client](../tests/reports/remote-floating-20261018-123959-client.json),
[restored-enabled client](../tests/reports/remote-floating-20261018-124103-client.json),
[compilation/scope report](../tests/reports/remote-v574-compilation-scope-20261018-183711.json).
Earlier diagnostic runs are retained, including failures used to identify the
Tk-interpreter and tray-handle bugs; they are not the passing final runs.

## Manual remote-computer check still needed

1. Update PAFPlayer.py on the remote computer as well as the player computer,
   using V574 or a later version containing these fixes. Quit/relaunch the tray
   client, or use its reload-from-updated-source action.
2. Connect to the official player's host and port. Enable Floating Lyrics on
   this computer and the usual rainbow/Emojimaxx treatment.
3. Watch several successive timed lyrics, including Whip where available.
   An unchanged song must not repeatedly show its intro or hide its sung line.
4. Pause/resume, toggle lyrics off/on, and restart with lyrics already enabled.
   Check a real track transition and a disconnect/reconnect.
5. Exit the client and check for Tk variable/callback errors or icon-handle
   overflow tracebacks.

The automated runs used real local Windows processes and actual Tk state, not
mock windows. They did not visually inspect the user's remote display. The
Computer Use helper could not initialize, so appearance, long-running behavior
and real-network latency on that separate computer remain unverified.
