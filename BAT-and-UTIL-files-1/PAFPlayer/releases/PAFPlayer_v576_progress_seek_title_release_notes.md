# PAFPlayer V576 — progress color layers, instance seeks, and console titles

Released October 18, 2026.

## Changes

- **Progress Bar:** Invert order reverses spatial gradient sampling; Invert
  palette complements the RGB colors. These are separate saved booleans, so
  existing style and color mode numbers retain their meanings. Beat color
  overlay can blend any existing coloring mode over the base mode on musical
  onsets, including an American Flag overlay over Rainbow.
- **Command line:** A standalone timestamp in a second normal launch seeks
  the official running player over its authenticated single-instance handoff.
  Accepts `0:00`, `0:30`, `1:30`, `60s`, `120s`, `125s`, `-5s`, and `-1:30`.
  Negative values count from the end; out-of-range values clamp. Playing and
  paused transports both use the existing seek path. A lone timestamp with no
  official player fails clearly; `--instance` cannot retarget this handoff.
- **Console title:** The first track shows a five-second, half-screen rainbow
  PAFPLAYER title. Its 25 designs combine five pixel-lettering treatments and
  five color sweeps using the existing 2×4 DRCS art bank. Experimental Web
  Config provides a saved title selector and a five-second test. The custom
  dropdown keeps the preview visible while open, then ten seconds after close.
  Preview painting does not pause audio.
- **Startup text:** The `↩ Resuming playlist` line gains one leading space.
  The MonkeyMote listening line omits its former parenthetical; multiple
  simultaneous clients remain supported and are described in
  [the MonkeyMote guide](../docs/monkeymote.md).

## Validation and limits

Focused V576 regressions and selected existing progress, web, and playlist tests
passed. The full set of historical embedded tests has three pre-existing failures
also present in V575: a legacy FFplay seek-count assertion, a lyric source-string
assertion, and a missing `output_devices_mask` web schema choice. The V519
transport test cannot load its missing V518 baseline artifact. Actual terminal
DRCS rendering and interactive dropdown duration still require a live Windows
console/browser check. A negative timestamp needs a known track end. The
interactive seek still caps the decoder start fractionally before EOF, as prior
web seeks do.
