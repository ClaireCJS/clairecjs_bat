# PAFPlayer V552 — channel marks and locked-bass detection

- Playback Channels now supports persistent Favorite and Default controls.
- Valid channel marks are Stereo, 5.1, 7.1, and Dolby Atmos 7.1.4.
- Windows lock detection now verifies access to the interactive desktop instead
  of assuming every `OpenInputDesktop` handle means the session is unlocked.
- Crossing the real lock boundary rebuilds the immutable FFmpeg filter chain at
  the current timestamp, applying/removing the configured low-shelf reduction.
