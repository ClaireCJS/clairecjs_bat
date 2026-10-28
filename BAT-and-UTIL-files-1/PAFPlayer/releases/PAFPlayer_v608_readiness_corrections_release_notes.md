# PAFPlayer V608 — readiness corrections

The first-run installer and `--readiness-check` now assess the file being
installed or checked. A valid Python file without PAFPlayer's bundled feature
modules fails the bundle check instead of inheriting a pass from the caller.

- Local playback requires both `ffmpeg` and `ffplay`. A missing `ffplay` now
  blocks launch instead of appearing as an optional warning.
- Tray-only control does not require Pillow or `send2trash`. Their absence is
  reported as an optional warning. JPEG artwork in the native tag viewer may
  need Pillow; optional old-artwork cleanup retains files if recycling is
  unavailable.
- No active configuration or media migration behavior changed. The installer
  still preserves the staged copy after a failed readiness check.

Regression checks cover candidate-bundle inspection, missing `ffplay`, and
tray-only package requirements. The checks are read-only; no physical audio or
remote Windows tray session was exercised in this release.
