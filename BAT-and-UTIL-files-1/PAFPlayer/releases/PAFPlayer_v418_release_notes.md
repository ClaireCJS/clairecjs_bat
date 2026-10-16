# PAFPlayer V418 — reliable browser playback detection

September 21, 2026. Build `2026-09-21-v418-browser-playback-detection`.

## What failed

The running V417 player reported `Playback monitor disconnected; retrying`, with no active external players. A separate Windows probe reported Chrome as Playing while the user reported YouTube playback. Browser detection is possible on this computer; the player's helper was failing, and its stderr was discarded. The specific cause of that old helper's exit was not recoverable from its status.

## Changes

- Browser/VLC audio detection now runs directly in a background Python thread through Windows Core Audio. Winamp playback state is also queried directly. Neither requires PowerShell, C# compilation, a browser extension, or remote debugging.
- The optional Windows media-session helper now supplies transport state only. It remains useful for silent/muted playback when the browser publishes it. Its failure cannot prevent positive native audio detection.
- Real audio from one tab can override another tab's Paused media-session report. A paused stream with no audio does not override transport state.
- Chrome, Opera/Opera GX, and Edge are recognized, including Edge's packaged application identity. The other previously supported browsers remain recognized.
- A failure on another endpoint no longer vetoes positive playback evidence. Stale evidence is discarded. Missing coverage cannot falsely release an automatic pause after a previously working media-session feed disappears.
- Helper exit codes and diagnostic messages are preserved and shown in the web playback section when fallback is in use. A hung helper is terminated and retried without blocking the native reader or playback thread.
- Existing manual pause/stop ownership and the configurable 15-second automatic-resume fade remain intact.

No browser audio is recorded. The detector reads process names, stream activity, peak levels, and published playback state on the same Windows computer. Browser audio is detected generally; this does not inspect or distinguish YouTube URLs from other sites. Video with neither an audio stream nor a Windows-published playback session cannot be identified by these mechanisms. Remote computers are not monitored.

## Validation

- 42 focused tests pass: 14 new browser/fallback/diagnostic tests, nine previous external-media tests, 13 V417 transport/download tests, one actual player-loop pause/resume integration test, and five embedded media/Winamp regression checks.
- Live native reads detected Chrome's active audio. 100 repeated COM enumerations completed in 1.547 seconds, with all COM references released by the reader.
- The combined live monitor reported Chrome active and generated `external-media-auto-pause` through the real coordinator.
- With helper launch deliberately disabled, native detection still reported Chrome active and healthy, with an explicit fallback diagnostic. No playback-control command was sent to the user's browser during these tests.
- Browser JavaScript syntax checks pass. Opera and Edge identity/decision behavior is covered by tests; they were not separately exercised with live video.
- The full historical 656-test suite was not rerun for this patch. Its previously documented failures remain tracked in the V417 notes.

Live observations: `pafplayer_v418_live_detection.json`. Focused test file: `test_play_audio_file_v418.py`. Restart PAFPlayer to replace the already-running V417 code and start the new native reader.

Windows API references: [audio session enumeration](https://learn.microsoft.com/en-us/windows/win32/api/audiopolicy/nf-audiopolicy-iaudiosessionmanager2-getsessionenumerator), [published media sessions](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession), and [COM threading](https://learn.microsoft.com/en-us/windows/win32/api/objbase/ne-objbase-coinit).
