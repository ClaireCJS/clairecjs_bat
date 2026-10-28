# PAFPlayer V606 — first-run copy and readiness diagnostics

## Installation

- Running a loose `PAFPlayer.py` on Windows creates a separate installation and launches it after required readiness checks pass. `--install` requests the same process from a development or installed copy.
- The destination is `C:\BAT\PAFPlayer` when `C:\BAT` exists, otherwise `%LOCALAPPDATA%\PAFPlayer`. Occupied names fall back to `PAFPlayer_v606`, then a timestamped name, then numbered collision suffixes. Existing directories and the source file are preserved.
- The installer stages the script, verifies SHA-256 and Python syntax, writes a short `PAFPlayer.md`, an installed usage guide, and an integrity marker, then publishes the new folder. It does not copy playlists or saved configuration. A failed required check leaves the installed copy available without launching playback.
- This sets up the application folder structure. It does not install Python, FFmpeg, missing Python packages, lock-screen integration, or screensaver integration. Those remain separate prerequisites or optional features.

## Diagnostics and wording

- `python PAFPlayer.py --readiness-check` prints every check with PASS, FAIL, or WARN and gives repair hints. It is read-only and can be rerun from an installed copy. Add `--tray-only` to check a remote tray computer without requiring local audio output or FFmpeg.
- `--readyness-check` is supported as an alias and points out the correct spelling.
- Emojimaxx leaves “passion” and “passions” as literal text. The unrelated “compassion” entry remains available.

## Verification and limits

The focused tests cover collision naming, source preservation, staged copy integrity, launch gating, argument forwarding, diagnostic output, marker drift, alias spelling, and Emojimaxx wording. The release also runs existing layout and Emojimaxx regressions, Python syntax checks, and bundled-source parity.

The installer cannot guarantee that every optional Windows integration works on a given machine. Readiness reports capabilities it can inspect; hardware availability, permissions, and playback still need an actual run. An abrupt process or power failure can leave a staging folder; no existing installation is overwritten.
