# PAFPlayer V765 — Simple preview focus and backwards playback

## Changes

- Keyboard-resuming a paused `--simple` preview now force-reclaims audio focus immediately before resume and pauses every other registered PAFPlayer instance, including a main player that resumed while the preview was paused.
- Added `#backwards` and `#backward` to toggle lossless reverse playback, and `#forward` to return to normal direction. The first backwards request starts from the selected track’s end.
- Reversed audio is generated once per source revision with FFmpeg and cached under `runtime\cache\reversed-audio`. A preparation failure returns to forward playback and displays the reason.
- Playback position, seeks, karaoke, and the progress bar follow the reverse direction; the progress fill moves from the right. The HUD displays **Backwards Mode** in bright yellow.
- Ctrl+Alt+B remains assigned to the existing visualizer action.
- Added a Unique PAFPlayer features section near the top of the full documentation and linked the hash command reference.

## Runtime requirements

Backwards mode requires the FFmpeg executable already used by PAFPlayer. Its first use for each song waits for a lossless reverse-cache file to be prepared; later uses reuse that cache.
