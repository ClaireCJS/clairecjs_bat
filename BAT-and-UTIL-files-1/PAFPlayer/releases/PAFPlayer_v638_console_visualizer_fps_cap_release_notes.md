# PAFPlayer V638 — Console visualizer FPS cap

November 2, 2026

- Added a number field in Web configuration → Console Visualizer to set the
  maximum console spectrum repaint rate from 1 to 120 FPS. The default is 60.
- The value is saved as `ConsoleVisualizerMaxFps` in the existing global player
  settings and is restored on later launches. Changing it updates the running
  frame scheduler without restarting audio.
- The adaptive frame governor, diagnostic frame cap, and Steam game load
  reduction may paint below the chosen maximum. None can raise the console
  frame target above it. Browser visualizer timing is independent.
- Focused regression tests cover the default, saved value, validation, web
  control, and frame-target calculation.
