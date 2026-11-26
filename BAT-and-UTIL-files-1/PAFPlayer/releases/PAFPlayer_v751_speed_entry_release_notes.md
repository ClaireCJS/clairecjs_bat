# PAFPlayer V751 — direct speed entry

X/x now opens a speed menu instead of stopping playback. Typing 4 and Enter sets 4×. Decimal presets, an optional x suffix, Backspace, = reset and Esc cancel are supported. The menu draws immediately and handles already-buffered input without a key-flush delay. It stays within the existing live prompt loop and applies through existing speed-change/restart handling during playback and pause. Help and usage identify X as speed entry.

V750's simple-preview global-pause ownership fix remains included. Validation covers parser boundaries, actual menu input, full playback application, interrupt regressions and simple-mode isolation.
