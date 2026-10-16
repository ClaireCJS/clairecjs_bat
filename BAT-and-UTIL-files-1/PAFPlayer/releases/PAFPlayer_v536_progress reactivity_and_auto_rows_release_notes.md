# PAFPlayer V536 — progress reactivity and automatic visualizer height

Released October 13, 2026.

- Adaptive progress flashing again consumes the current spectrum during file
  playback, falling back to the precomputed beat timeline only when necessary.
- Color-intensity flashes now have a visible playhead-to-tail brightness decay.
- Artwork Seaming favorite/default controls accept all strategies, including the
  0-based unchanged-output choice.
- **Tallest** is renamed **Set to tallest** for its one-shot behavior.
- **Auto-set to tallest** persistently follows terminal and HUD geometry changes.
