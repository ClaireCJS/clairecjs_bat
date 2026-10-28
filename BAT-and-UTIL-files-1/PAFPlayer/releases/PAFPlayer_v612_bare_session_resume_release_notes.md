# PAFPlayer V612 — bare session resume

Run `PAFPlayer resume` after a crash or reboot to reopen the last bookmarked
playlist and restore its song and playhead through the existing playlist logic.
Checkpoints now include the playlist path. This reuses the official
single-instance handoff and does not create another playback mechanism.

With no arguments, help ends with a blinking, double-height resume hint when the
saved playlist still has usable entries. Terminal support determines whether
blink and double-height effects are visible.

An older bookmark lacks the playlist identity: launch that playlist explicitly
once after upgrading. A missing or empty playlist produces a clear error and
does not start playback. Resume still uses the existing approximately two-second
checkpoint cadence. It restores the playlist, selected track, playhead and saved
next-track hint; it does not serialize every transient UI/window state.
