# PAFPlayer V480 — keep playing after current-track removal

Fixed the Delete-key playlist-removal behavior. After confirming removal of
the currently playing track, PAFPlayer now removes it from playlist
membership while allowing the current audio to continue normally.

The decoder is no longer stopped and playback no longer jumps immediately to
the next track. The behavior is also applied to the paused Delete-key path and
the already-confirmed web playlist action.

Validation: Python compilation and focused source checks passed for both
active and paused removal paths.

Changed files:

- `../PAFPlayer.py`
- `../docs/playlist-controls.md`
