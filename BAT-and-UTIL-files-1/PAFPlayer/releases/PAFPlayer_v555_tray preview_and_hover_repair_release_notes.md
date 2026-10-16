# PAFPlayer V555 — tray preview and hover repair

- Tray icon chooser pictures now use their intended 32×32 drawing canvas, so
  the symbol is centered and visible before a choice is made.
- Tray mouse callbacks decode the event from the low word of `lParam`, restoring
  the optional album-art/full-information card on newer Windows shells.
