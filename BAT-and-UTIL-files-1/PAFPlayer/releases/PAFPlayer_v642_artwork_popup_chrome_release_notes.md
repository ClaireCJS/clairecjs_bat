# PAFPlayer V642 — artwork popup chrome

Released November 4, 2026.

## What changed

- One persistent header row: a large Artist - Song title beside one 🌐 button.
  Long titles ellipsize horizontally; no second row or overlapping caption.
- 🌐 opens the current player's `#artworkPopupSection`. The web scroller now
  resolves that anchor on initial load and when the URL fragment changes.
- The title/web-button bar stays visible when unfocused, as requested. The
  custom focus border becomes transparent; the native Windows caption, frame
  and shadow are removed permanently instead of clipping their outer two pixels.
- Drag the title to move; drag focused borders/corners to resize. Ctrl retains
  square resizing. Right-click the title for Always on top or Close; Alt+F4 works.
  Existing lyric zoom keys, taskbar access, settings and remote-tray behavior remain.

## Cause

The old implementation packed the title and buttons into separate rows while
retaining a normal native caption. Focus loss only changed the artwork wrapper
color; removing extended edge flags and clipping two outer pixels could not
remove the remaining native caption/frame. V642 uses a stable borderless Tk
window and a single custom header. Private, pointer-safe Windows API bindings
avoid interference with other popup callbacks, and the foreground query is
cached instead of rebuilding its binding on every focus poll.

## Verification

- **25/25 tests pass**, no skips: actual Tk layout and font sizing, long-title
  truncation, one-button URL, focus/geometry roundtrips, title dragging, minimum
  resize bounds, typed native APIs, URL-anchor navigation, and related existing
  artwork/floating-lyric geometry and solution-color tests.
- All **27 embedded modules compile and match their sources**; all **eight web
  scripts** pass Node syntax checks. Two historical border tests were updated
  to protect permanent border removal instead of the superseded pixel-clipping
  implementation; their debounce/non-reentrancy checks remain.
- Final source ran in an isolated popup on the interactive Windows account.
  Both focus states retained the same HWND and 900×620 position/size. The native
  style has no caption or thick frame. The header had exactly one label and one
  button, with non-overlapping bounds, and stayed visible on focus loss. Border
  colors changed gray → transparency key with **zero callback errors**.
- Screenshot capture failed with `window capture timed out: timed out waiting
  on channel` on both the popup and the normal test window; a direct button UI
  click also lacked coordinate geometry. The button callback was verified in a
  real Tk unit test, and hash scrolling in Node. Pixel-level visual confirmation
  and clicking through to a running player's web UI remain manual checks.
- No audio was started/stopped and no household-player commands or preferences
  were changed. All test fixtures and earlier failed attempts are retained.

[Test report](../tests/reports/v642-checks-20261104-084801.json) ·
[Interactive native trace](../tests/reports/v642-ui-20261104-084825.jsonl) ·
[Behavior and manual check](../docs/window-shortcuts.md#v642-artwork-popup-header-and-focus-border)

Restart PAFPlayer (and any tray-only computer using its own older copy) to load
V642. The currently running player is not hot-patched.

Source SHA-256: `227f607b020d7f153761ccac00c6dec97c92687979a67896126df828ada65f48`.

## Files and root audit

The release Python file is a non-overwriting, hash-verified copy of the tested
active source. Documentation and changelog are updated; required backups were
verified as siblings before archiving. The complete path inventory is
`tests/reports/v642-change-manifest.json`.

The PAFPlayer, lockscreen and screensaver roots contain only active code,
required project inputs, or retained runtime/user sidecars. No obsolete files
needed moving and no files were deleted. **No literal C:\BAT paths changed.**
`play_audio_file.py` was not modified.
