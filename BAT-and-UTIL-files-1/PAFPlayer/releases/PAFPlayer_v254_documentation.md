# PAFPlayer V254 — readable web karaoke and selectable floating lyrics

**Release:** PAFPlayer V254  
**Build ID:** `2026-08-19-v254-readable-web-and-selectable-floating-lyrics`  
**Baseline:** PAFPlayer V253 (`59b78966a385fff2d04c7e489b966281378fc3e74923582f02a18173d9f93e8b`)  
**Prepared:** 2026-08-19 (America/New_York)

V254 is a focused UI-regression repair built directly from V253. It does not change V253's live visualizer-input system or the broader V252 feature set.

## Web Karaoke readability

V253's Auto-size fit search could inherit an old very small saved lyric-splitter height. The fitter was then correctly fitting the text into the wrong tiny box, which produced the postage-stamp karaoke shown in the supplied screenshot.

V254 keeps the bidirectional fit search, descender guard, glow scaling, and manual splitter persistence, but adds a viewport-aware **readable automatic height floor**. Auto-size now:

- reserves at least 132 px, scaling up toward 19% of the browser viewport and capping the automatic floor at 260 px;
- ignores stale/manual lyric heights that are clearly below that automatic floor;
- still honors a deliberate larger manual lyric region;
- then binary-searches the lyric font upward/downward inside that usable region.

The result is that Auto-size once again means “make the lyric use the available karaoke area,” rather than “make the lyric technically fit inside an accidentally tiny remembered strip.”

## Floating lyric selection and size

The floating lyric regression had a related geometry feedback loop. Runtime floating lyrics deliberately collapse to a compact transparent mask. V253 could accidentally treat that compact runtime rectangle as the next typography/layout rectangle when the lyric was clicked. That made later lines progressively smaller, and could leave the explicit **Make floating lyrics window appear** action apparently doing nothing because the window was only a tiny transparent content mask.

V254 separates those concepts again:

- the compact transparent runtime mask remains compact when the lyric is merely being displayed;
- a click on an opaque floating lyric now expands it around its current center into the remembered **editing/layout rectangle**, gives it edit chrome, raises it, and focuses it;
- tiny legacy layout sizes are migrated to a readable monitor-relative default (roughly 46% of screen width × 18% of screen height, bounded to 520–960 × 150–300);
- only a genuinely useful saved edit rectangle (at least 360 × 100) is reused as a typography constraint;
- the explicit **Make floating lyrics window appear** action now enters this visible/selectable edit state even when the current lyric is empty;
- after focus leaves, the window returns to the compact transparent presentation while preserving the user's edit-box size and visual center.

This also fixes ordinary lyric clicking as the selection/manipulation gesture instead of requiring Control merely to recover a microscopic window.

## Verification

- Python compilation: **passed**.
- Embedded regression suite: **521 tests run, 519 passed, 2 expected platform-dependent skips, 0 failures**.
- Extracted web JavaScript: **`node --check` passed**.
- Normal and descriptive V254 Python files: **byte-identical**.
- ZIP extraction and SHA-256 verification are release gates for the packaged artifact.

Live Windows/Tk focus, native floating-window hit testing, browser viewport behavior, and actual monitor DPI still require the normal Windows smoke check.
