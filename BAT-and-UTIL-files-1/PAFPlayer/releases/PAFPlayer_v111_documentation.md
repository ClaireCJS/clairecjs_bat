# PAFPlayer V111 — queued inserts, global volume, stable Last play, and restored documentation

**Build ID:** `2026-08-09-queued-inserts-global-volume-and-stable-hud-v111`

## Behavior changes

- INS-added tracks now enter an explicit play-next queue. Multiple selections are randomized among themselves only when shuffle is active, and ordinary queue/history shuffle resumes after the manual queue drains.
- Shift+INS uses a multi-select Windows file picker.
- Ctrl+Alt+Up and Ctrl+Alt+Down are deliberate global volume hotkeys (±5%) and work while another application has focus.
- Playback speed resets to 1× at process startup, clean new-playlist relaunch, and every successful manual playlist insertion.
- `Last play` is a track-start snapshot. The 33% local-history write and learned action still update SQLite immediately but do not change `Never` to `1min` or reflow the current HUD.
- Removing that history-triggered reflow eliminates the duplicate `Dir:` row shown in the supplied screenshot.
- Plain and ANSI cell-aware truncation close unmatched parentheses, brackets, braces, angle brackets, and paired quotes with the matching final character.

## Documentation changes

- `PAFPlayer_changelog.md` is now the detailed release/history ledger.
- `play_audio_file.md` is current operational documentation, with historical/change narration removed from its body.
- The manual ends with exactly one summary line for every numbered version through V111.
- Twenty-eight recovered real-session and controlled visual-reference assets are restored with local links and descriptive filenames.

## Verification

The embedded suite contains six new V111 regression contracts covering release identity, delimiter-safe truncation, immutable per-visit Last play, single Dir renderer, multi-select play-next insertion, startup/playlist/insert speed resets, and global volume polling. Python compilation, the full embedded suite, image-link validation, changelog/manual structure checks, byte identity, checksums, and ZIP integrity are release gates.
