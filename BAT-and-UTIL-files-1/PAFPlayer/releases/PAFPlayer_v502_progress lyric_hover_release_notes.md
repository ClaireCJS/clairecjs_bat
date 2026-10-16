# PAFPlayer V502 — web progress lyric hover

- Hovering over the web playback progress bar shows the seek time and the lyric that Web Karaoke would display at that point. Clicking the bar still seeks.
- The preview uses the published lyric timeline, trimmed playback start, and karaoke offset. It works whether playback is running or paused.
- During a blank interval, the most recent lyric remains in the preview at 50% opacity for five seconds after it disappears. At later times the tooltip says no lyric is available.
- The tooltip sits outside the clipped progress bar and is hidden when the pointer leaves, the page loses focus, or the page becomes hidden.
- Lyrics are assigned as text, so lyric content is never interpreted as HTML.

The preview depends on PAFPlayer having a lyric timeline for the current track. It does not infer lyrics for tracks without one.
