# PAFPlayer V634 — SIXEL confirmation and quiet error sound

November 1, 2026

- Enabling the experimental SIXEL visualizer in web configuration now needs
  two separate confirmations. Cancelling either sends no toggle action and
  leaves the checkbox off. Disabling it needs no confirmation.
- A playback instance that starts with SIXEL enabled prints a console warning
  with the session-only `--no-sixel-visualizer` escape. A second normal launch
  that forwards to the official instance does not print a misleading startup
  warning.
- The optional Wilhelm error sound now uses FFplay volume 1%, one tenth of its
  prior 10% playback level. Its saved `ErrorSoundEnabled` preference, bundled
  recording, popup, Windows notification, and per-file alert deduplication are
  unchanged.
- V633's bounded SIXEL output was confirmed in a live Windows Terminal run:
  HUD frames stayed in place with SIXEL enabled.

Focused tests execute the web toggle handler for both cancellation stages,
successful enablement, and immediate disablement, and cover the conditional
startup warning and quieter FFplay command. Python syntax, existing relevant
tests, and release-copy parity are checked separately.

This cannot guarantee identical SIXEL behavior in every Windows Terminal,
font, zoom level, or shell implementation. The startup warning is console
output; it is not a blocking dialog.
