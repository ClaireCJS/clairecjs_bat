# PAFPlayer V754 — arbitrary speed multipliers

X entry accepts any positive finite floating-point multiplier, including decimal and scientific notation, rather than limiting values to PLAYBACK_SPEEDS. Optional x/× suffixes, reset and cancel remain supported.

A separate session-local custom-speed value feeds decoder startup/restarts, playback position, seeking, paused clocks, lyric timing and visible speed feedback. It persists across tracks without modifying the dropdown preset list. Selecting a preset clears the custom value, including when the nearest preset index already matched; reset returns to 1×. Speed color uses the nearest palette entry without requiring the actual multiplier to be a preset.

Tests verify custom parsing and buffered menu entry, exact 1.37× delivery to decoder command construction, next-track retention, existing menu/reset behavior, inline interrupts and playback isolation. Syntax and release/source parity are checked.
