# PAFPlayer V707 — Floating Lyrics centering focus fix

Released November 13, 2026.

The Floating Lyrics centering commands no longer temporarily enable opaque edit
chrome or call `focus_force()`. They raise and position the transparent runtime
window directly, save its geometry, request a repaint, and retain a 250 ms guard
against delayed focus notifications.

This removes the persistent focused/unfocused strobe after **Center over
visualizer** while preserving ordinary glyph-click editing. No synthetic mouse
click is generated.

Focused source tests verify that both programmatic centering paths avoid forced
focus and edit mode. Existing edit-mode geometry and focus-loss fail-safe tests
also pass.
