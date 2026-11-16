# PAFPlayer V643 — artwork karaoke fit

Released November 5, 2026.

Artwork karaoke now expands to the largest fitting size inside the canvas
below the header. The prior 8.5%-of-window/260-point ceiling kept short cues
small. Both native vector text and Pillow text now fit the available space,
reserve shadow and emoji-answer margins, and wrap longer cues. Font fitting
remains logarithmic; cached fonts and the native rendering fast path remain.

Default 100% zoom means full fit. Existing zoom shortcuts reduce the fitted
size down to 50% or restore it up to 100%. Saved values above 100% are accepted
as full fit; one zoom-out immediately reduces them. No configuration IDs or
stored preference formats changed. The title/web-button bar stays unchanged.

## Verification

- **36 tests pass, zero failures/errors/skips**: short/long cues, real Tk font
  and canvas bounds, Pillow masks, colored/monochrome emoji, answer spacing,
  manual zoom, 4K growth, bounded fitting work, native rendered text/shadows,
  and relevant V642 header/geometry and V641 solution-color regressions.
- The same new sizing tests reproduced the issue against V642 before editing.
- Python compilation and all **27 embedded-module/source parity** checks pass;
  all **eight generated JavaScript blocks** pass Node syntax checks.
- No audio, household-player commands, or live preferences changed. Test GUI
  assertions ran on the isolated Windows test desktop; live-song visual
  verification after restart remains manual.

[Test report](../tests/reports/v643-checks-20261105-145329.json) ·
[Behavior and manual verification](../docs/window-shortcuts.md#v643-artwork-karaoke-fills-the-window)

Restart the player, and any remote tray client using its own copy, to load
V643. If old manual zoom is below 100%, Ctrl+= restores full expansion.

Source SHA-256: `510fed42f17d8a601eb16f6251c665edc5b355c68ea31a0c716dd67e7347e9cf`.

## Files

The release copy is new and hash-identical to the tested active source.
Required sibling backups were verified before replacement, then archived as
required. Root audits found only active code, project inputs and runtime/user
sidecars in PAFPlayer, lockscreen and screensaver. No deletions or cleanup moves
were needed. `play_audio_file.py` is unchanged. **No literal C:\BAT paths changed.**
The complete file inventory is in `tests/reports/v643-change-manifest.json`.
