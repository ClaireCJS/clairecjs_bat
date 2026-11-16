# PAFPlayer V637 — Web Karaoke and playback controls

November 2, 2026

- Auto-Expand Lyric Size now checks the rendered character bounds against the
  lyric panel as well as the element's scroll dimensions. Very large glyphs can
  extend outside their CSS line boxes; V636 did not account for that.
- Dragging the configuration panel boundary now resizes the lyric panel even
  when a larger height was reserved earlier. The fitter responds to that size.
- A click on the web progress bar moves the display immediately. The display
  reconciles with the owner's playback clock once the seek takes effect. Audio
  seek latency can still vary with decoder startup or a busy player loop.
- Console and taskbar lyric titles expire after the existing 15-second maximum
  during long gaps, including sidecars with a long explicit cue end. The web
  lyric timeline uses the same cutoff.
- Inter-track silence/overlap is editable as -5 to +5 seconds beside the slider.
  Its saved configuration ID remains `inter_track_timing_ms`. Positive values
  add silence. Negative values remain saved requests because the renderer does
  not yet mix adjacent tracks.
- Web configuration tabs now follow the sections' actual page order.
- A focused real Microsoft Edge regression tests short and wrapped Portuguese
  lyrics in a 3840 × 2160 browser viewport and checks that visible text stays
  inside the lyric panel. Other focused tests cover resize, tab order, seeking
  feedback, seconds entry, and lyric expiry.
