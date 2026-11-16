# PAFPlayer V645 — artwork window controls

Released November 6, 2026.

- Focused borders now use standard Windows horizontal/vertical/diagonal resize
  cursors. The hit areas used for cursors and dragging are the same.
- A focus-only □ / ❐ button overlays the right end of the song title. It
  maximizes/restores without altering native border styles or the header layout.
  The title and web button remain visible when focus leaves.
- Maximize fills the current monitor's work area. Restore returns to the exact
  normal rectangle, or a safely clamped rectangle if its monitor disappeared.
- While maximized, first restore to drag/resize; idle gallery and artwork
  compaction cannot move/shrink it. Monitor/work-area changes are handled.
  Saved placement remains the normal rectangle, including on close/restart.
- No configuration IDs, playback behavior or existing lyric fitting changed.

## Verification

**44 tests pass, zero failures/errors/skips.** Tests exercise actual Tk cursor
names and event handlers on all eight border positions, focused control
visibility without reflow, drag cursors, exact restore, negative monitor
coordinates, removed monitors, failed positioning, and saved normal placement.
A real Windows native-window test maximized to the reported monitor work area
and restored the exact original rectangle with the same borderless HWND.
Relevant header/border and karaoke fitting tests remain green.
Python compilation, all 27 bundled-module/source comparisons, and all eight
web-script syntax checks pass.

An isolated popup ran under the interactive Windows account: 160 samples
contained both focus states and matching maximize-button visibility, the same
HWND and 900×620 geometry, no native caption/resize-frame bits, and no callback
errors. Automated activation reported `failed to activate captured window`;
a refreshed screenshot reported `FrameArrived timed out: timed out waiting on
channel`. No stale coordinates were used. Pointer appearance and manual mouse
clicking of the button remain visual checks after restart. Tests did not start
or command playback or change live preferences.

[Test report](../tests/reports/v645-checks-20261106-114304.json) ·
[Interactive trace](../tests/reports/v645-ui-20261106-114122.jsonl) ·
[Behavior and manual procedure](../docs/window-shortcuts.md#v645-resize-cursors-and-focus-only-maximize)

Restart the player and any remote tray client using an older copy for V645.
The release copy is new and SHA-256 identical to the tested source:
`10023982c74ef26fc41305dac1ffc8ff3653eec803a31462562a10aea6ed0535`.

Required replacement backups were verified as siblings before edits and
archived as required. The project, lockscreen, and screensaver root audits found
only active inputs/runtime sidecars; no obsolete files needed moving/deletion.
No literal C:\BAT paths changed. `play_audio_file.py` is unchanged.
See `tests/reports/v645-change-manifest.json` for the affected path inventory.
