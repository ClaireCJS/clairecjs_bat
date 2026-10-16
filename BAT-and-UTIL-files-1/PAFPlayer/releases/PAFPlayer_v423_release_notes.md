# PAFPlayer V423 — paused HUD controls and asynchronous console feedback

September 21, 2026. Build `2026-09-21-v423-hud-pause-reasons-async-feedback`.

## HUD details toggle works while paused

`Ctrl+Alt+/` already toggled the optional main-HUD ReplayGain, playlist, and tag
rows during active playback.  The paused input loop lacked its matching action
handler, making the shortcut appear one-way after playback was paused.  It now
uses the same toggle/reflow/redraw path in both states.

## Console feedback is non-blocking

Visualizer overlay messages are presentation-only.  A new control action now
explicitly resets the existing overlay's fade state, so its message replaces an
older one at the next visualizer paint.  It does not wait for the prior hold or
fade to end and does not own the player action/input loop.  Repeated volume
changes therefore immediately show the newest volume message.

## Pause status in Help

When playback is paused, `?`/F1 now includes `⏸ Paused` in the diagnostic
surface.  An automatic external-media pause appends the same recorded source
evidence used by the console popup and trace log (for example, a playing media
session, active/audible audio session, or Winamp IPC state).

## Saved artifacts

- Canonical player: `play_audio_file.py`
- Versioned snapshot: `play_audio_file_v423_hud_pause_reasons_async_feedback.py`
- This description: `play_audio_file_v423_release_notes.md`

Restart PAFPlayer to load V423 if it is already running.
