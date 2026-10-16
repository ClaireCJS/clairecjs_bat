# PAFPlayer V563 — shared remote floating-lyrics renderer

- Removes the tray-only client's plain-label lyric window.
- Uses the exact `ExternalAlbumArtWindow` floating renderer on player and remote
  screens.
- Feeds the renderer synchronized remote timestamps, cue progress, track
  identity, speed, and play/pause/stop state.
- Redirects only its preference persistence to endpoint-specific roaming
  AppData JSON.
