# PAFPlayer V422 — external-media pause reasons

September 21, 2026. Build `2026-09-21-v422-external-media-pause-reasons`.

## What changed

Automatic external-media pauses now keep an auditable explanation in the
PAFPlayer trace log.  Each `external-media.pause` event records:

- the trigger (`new unacknowledged external playback`),
- active source families,
- per-source qualifying evidence (Windows media-session state, an active audio
  session, an audible audio session that overrides a conflicting media-session
  state, or Winamp IPC playback),
- monitor backend/known/degraded/error status, and
- PAFPlayer's playback position.

The console visualizer transient popup now shows that same concise source
evidence instead of only naming the application.  For example: `Chrome: media
session Playing` or `Chrome: audible active audio session (overrides
media-session status)`.

Automatic resume records the completed quiet-period trigger in its
`external-media.resume` trace event and shows the quiet interval plus fade
duration in the console popup.

## Saved artifacts

- Canonical player: `play_audio_file.py`
- Versioned snapshot: `play_audio_file_v422_external_media_pause_reasons.py`
- This description: `play_audio_file_v422_release_notes.md`

## Validation

- Python compilation and `--version` are checked before release.
- The snapshot SHA-256 is required to match the canonical player.

Restart PAFPlayer to load V422 if it is already running.
