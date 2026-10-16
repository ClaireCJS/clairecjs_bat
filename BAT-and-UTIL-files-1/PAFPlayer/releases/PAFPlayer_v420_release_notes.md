# PAFPlayer V420 — external-media priority after Play/resume

September 21, 2026. Build `2026-09-21-v420-external-media-priority`.

## Failure and repair

The running V419 status showed Chrome active, detection healthy, automatic pause enabled, and PAFPlayer still playing. Trace history contained pause/resume actions. The coordinator's `override_until_quiet` latch explained that combination: Play/resume bypassed automatic pause until every external player was confirmed quiet for 1.5 seconds. A continuing browser session could leave that bypass active across songs and even suppress a newly started VLC player. Play during monitor startup could also arm the bypass before any positive detection.

V420 removes that bypass. While **Pause for VLC, Winamp and browser media** is enabled, detected external playback retains priority. Pressing Play while other media is active keeps PAFPlayer automatically held and requests resumption after that media finishes. Turn the setting off to permit simultaneous playback.

Manual Pause and Stop still remain held after external media finishes. Automatic holds still resume after 1.5 seconds of confirmed quiet, with the configured fade (15 seconds by default). The web explanation reflects this behavior. Status now includes `external_media_decision`, and diagnostic traces distinguish `external-media.pause` / `external-media.resume` from ordinary pause toggles.

This release preserves the V419 album-art emoji-spacing change already present in the workspace, as well as the V418 native detector and V417 Winamp-compatible URLs/downloads.

## Validation

- 43 focused tests pass: seven new priority/player-loop regressions, nine external-media tests, 14 detection/fallback tests, and 13 web transport/download tests. The old test that required Play to bypass priority was updated to the corrected behavior.
- Full-loop regression exercises Chrome detection, Play and Space attempts during the automatic hold, VLC joining, both sources finishing, a 15-second fade, another VLC interruption, and a manual hold that must not auto-resume.
- Live Chrome test: real Windows detection caused the actual PAFPlayer loop to stop an `IsolatedWaveOutProcess` (running before the pause, exited afterward). Play remained held. Test audio volume was zero; the user's existing player/browser was not controlled.
- Live VLC test: a separate hidden VLC instance played a silent WAV. The real PAFPlayer loop stopped its real audio worker and kept Play held. Chrome was filtered out only inside the test to establish that VLC independently caused the result. Only the test VLC instance was closed afterward. Earlier isolated VLC launches did not expose a stream until first-run prompts were explicitly disabled in the test launch.
- Reports: `pafplayer_v420_live_player_check.json` (Chrome), `pafplayer_v420_live_player_check (1).json` (VLC).

The live checks verify actual playback-worker shutdown, not only detector output. They do not hot-patch the already-running V419 user session: restart PAFPlayer and confirm V420 in its web status/version badge. The historical full suite was not rerun for this focused repair.
