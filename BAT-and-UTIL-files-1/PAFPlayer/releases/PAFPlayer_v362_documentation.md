# PAFPlayer V362 — full `--emojimaxx` terminal preview

**Release:** PAFPlayer V362  
**Build ID:** `2026-08-29-v362-emojimaxx-full-cli-preview`  
**Baseline:** uploaded V361 (`2026-08-29-v361-eighteen-two-circled-digits`)  

## Change

`--emojimaxx "text"` (and its `--emojimax` alias) now emits three increasingly faithful terminal previews and then exits without starting playback, history, artwork, or the web server.

1. It begins with one ordinary-height blank line, then prints the ordinary Emojimaxx solution.
2. It prints two ordinary-height blank lines, then prints the same solution as DEC double-height rows. Every logical line is emitted as a correctly paired `ESC # 3` top row and `ESC # 4` bottom row.
3. It prints two more ordinary-height blank lines, then prints a live-style current karaoke rendering using the saved `KaraokeStyle` and `KaraokeTreatment`, with Emojimaxx forced on, the same half-terminal-width wrapping/centering geometry, full-brightness treatment coloring, and the same dark-teal current-line highlight used by live console karaoke.

Every non-double-height row emitted by this CLI preview is explicitly prefixed with `BIG_OFF` / DEC `ESC # 5`. After the final double-height karaoke row, V362 also writes a final `BIG_OFF` without adding another newline so the shell prompt cannot inherit `#4`/double-height state.

For long text, the final live-style preview represents the first current-cue page, matching PAFPlayer's live cue-start behavior (up to two logical wrapped lines / four physical DEC double-height rows).

## Verification

- `python -m py_compile`: passed.
- Three targeted `--emojimaxx` tests: passed.
- New regression test verifies the initial `BIG_OFF` blank, ordinary solution, explicit `#3/#4` raw double-height pair, two `#5` separator lines, live current-line highlight, and final `BIG_OFF` shell reset.
- Full embedded suite on V362: 583 tests, 30 failures, 2 skipped.
- Full embedded suite on the unmodified uploaded V361 baseline: 582 tests, the same 30 failures, 2 skipped.
- Therefore V362 adds one passing regression test and introduces no new embedded-test failures relative to V361.

No playback, visualizer, shuffle, web UI, audio, history, artwork-window, or normal live-karaoke behavior is intentionally changed.
