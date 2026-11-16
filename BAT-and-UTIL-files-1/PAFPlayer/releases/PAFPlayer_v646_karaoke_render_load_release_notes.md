# PAFPlayer V646 — karaoke render load

Released November 9, 2026.

Inherited Emojimaxx answer colors used a Python pixel-by-pixel search on every
refresh. A colored emoji can leave its monochrome glyph mask completely empty,
forcing two whole-region scans. Large expanded lyrics made this expensive on
the shared interpreter while console, artwork, and floating lyrics ran together.

V646 uses Pillow's native mask operations to find the same color. It retains
the original thresholds, leftmost-column selection, center-row tie breaking,
clipping, and fallback. It reads at most one pixel through Python. No new cache,
frame queue, process, setting, or dependency is introduced.

Artwork draws a new lyric immediately, cancels the previous animation timer,
and waits its normal 50/90/140/150/220 ms cadence before recoloring. This avoids
the old zero-delay second repaint. Console refresh limits, lyric clocks,
playback/audio code, font fitting, effects, and configuration IDs stay intact.

## Measurements and checks

Unprofiled synthetic inherited-color lookup medians, measured on this computer:

| Region | V645 | V646 |
| --- | ---: | ---: |
| Empty emoji mask, 300 × 160 | 49.10 ms | 0.061 ms |
| Empty emoji mask, 900 × 320 | 332.00 ms | 0.269 ms |
| Left padding, 300 × 160 | 8.06 ms | 0.341 ms |
| Left padding, 900 × 320 | 53.17 ms | 1.787 ms |

Both artwork image hashes and all selected colors match. These are helper
timings, not achieved FPS. Large-image Tk uploads still cost about 28 ms in the
1920-wide fixture; other render/terminal costs and game load remain possible.
The November 6 profile identified the hotspot but has profiler overhead; the
table uses the November 9 unprofiled comparison only.

**129 relevant tests: 122 passed, seven failed, zero errors/skips.** The same
seven failures occur on unchanged V645 (112 passed out of 119). Ten new tests
pass, including 300 deterministic color-equivalence cases, bounded pixel calls,
timer cancellation, immediate cues, and unchanged size-dependent cadence.
Older failing tests concern historical UI/source contracts and removal counts;
they are retained and are not reported as passing. This is a relevant subset,
not the complete historical suite. All 27 module/source parity comparisons,
Python compilation, and eight generated web-script syntax checks pass.

Tests use preserved isolated fixtures. Guards blocked attempted live registry
and C:\logs writes from older tests. No live playback commands or preferences
were changed. [Comparison report](../tests/reports/v646-comparison.json);
[current checks](../tests/reports/v646-checks-20261109-011750.json);
[baseline checks](../tests/reports/v646-checks-V645-20261109-011937.json).

## Try the release

Restart PAFPlayer from the updated workspace, and update/restart any remote
tray client that renders lyrics. Enable console, artwork, and floating lyrics;
use a timed song with Emojimaxx answers and inherited answer coloring. Compare
FPS and visible stalls at the same window sizes/settings, including full-size
artwork, repeated lyric changes, pause/resume, and seeking. Confirm all three
displays remain synchronized and answer colors still match their settings.
Live sustained FPS with all three displays has not yet been verified.

The new release copy is `PAFPlayer_v646_karaoke_render_load.py` and matches the tested active source:
SHA-256 `9c0c52dddcb8b6971cf8c269b67703e1de33fe12ee75c6d7e7d28245cf6beb65`.

Verified sibling backups precede replacements and are retained in the required
archives. Root audits of PAFPlayer, lockscreen, and screensaver found only active
inputs/runtime sidecars; nothing required deletion or relocation.
No literal C:\BAT paths changed. `play_audio_file.py` is unchanged.
The full path inventory is `tests/reports/v646-change-manifest.json`.
