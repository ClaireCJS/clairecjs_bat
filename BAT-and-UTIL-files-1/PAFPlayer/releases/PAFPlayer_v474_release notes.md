# PAFPlayer V474 — optional visual screensaver sidecar

Adds a separate `PAFPlayer.scr` with artist — song, current timed lyric, primary
album cover, and adjustable cover brightness. **Visual Screensaver** is a new,
explicit, off-by-default setting with Show and Close controls. Existing Windows
media settings and configuration IDs remain unchanged. Includes the current
V473 player changes rather than reverting to an earlier release.

The `.scr` supports Windows fullscreen, embedded preview, and configuration
arguments. It runs below normal priority, reads a small loopback-only endpoint
at up to five updates per second, and fetches artwork only when its revision
changes. A separate activity signal enables lyric publishing without waking
browser spectrum processing. Rendering/image decoding are outside playback.
Response sizes, timeouts, retained bitmaps and the GUI mailbox are bounded.

A connected but disabled player is explicitly identified in the preview.
The reported detection problem was investigated against the live V473 process:
both the player and screensaver endpoints responded on port 666, while the
screensaver option was disabled. A separate native preview-parenting defect was
fixed and the actual compiled `.scr` now passes preview process lifecycle tests.
Disconnected players clear old lyrics/artwork and show a waiting view.

The first version uses the primary monitor. Windows owns idle activation and
sign-in policy; Show does not lock Windows or replace its native lock screen.
System screensaver selection and lock settings are not changed automatically.
Unsupported artwork formats can fall back to text without affecting playback.

Validation: **77 focused Python tests and 29 native checks passed**, including
HTTP authorization, persistent settings/backup behavior, existing configuration
values, audio-ending and cache regressions, response limits, corrupt-art caching,
100,000 coalesced updates, Unicode, brightness, and a real `.scr` preview process
with parent teardown. These are focused checks, not a new claim that the complete
historical suite is green. Secure idle activation, actual listening and hours of
live playback remain manual verification steps.

Files follow the reorganized project: player and runner in `PAFPlayer`, shared
tests in `PAFPlayer/tests`, snapshots and records here in `releases`, and sidecar
sources/build/tests/artifacts in `PAFPlayer/screensaver`. The repository launcher
supports both the new nested project and an existing flat installed player.
`play_audio_file.py` is unchanged.

See the [architecture, limitations and manual procedure](../screensaver/README.md).
