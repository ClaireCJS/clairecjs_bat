# PAFPlayer V561 — tray lyric tooltip

- Replaces Windows lyric notifications with a PAFPlayer-owned tooltip above the
  notification-area icon.
- Updates automatically for every changed sung line without requiring hover.
- Uses a bright-yellow, wide, word-wrapped presentation.
- Never activates and passes clicks through, so it cannot block the tray icon.
- Positions from the real tray-icon rectangle and supports taskbars on any edge.
- Hides for blank lyrics, disconnects, disabled settings, and tray shutdown.
- Applies to both the official tray and `--tray-only` clients.
