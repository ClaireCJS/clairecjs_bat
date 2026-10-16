# PAFPlayer V519 — leaner visualizer output and earlier lock-screen lyrics

Released 2026-10-10. Build `2026-10-10-v519-lean-visualizer-early-lock-lyrics`.

The observed V518 sample spent 63 ms writing each visualizer frame and 2.5 ms
generating it. V519 skips unchanged artwork spans when cheaper and only resends
changed color channels. It preserves every final glyph/RGB value, initial full
frames and row-alignment guards. Identical synthetic frames used **42–64% fewer
output bytes**, with slightly faster encoding. Real in-game FPS remains unmeasured.

Lock-screen lyric selection now leads by **250 ms** while playing, scaled by
playback speed. Pause/stop, seeks and lyric offsets are covered. Other lyric
displays and audio timing are unchanged. Windows still controls presentation.

**Launch V519 to load both changes.** The signed companion is installed as
PAFPlayer Lock Screen V519, preserving its Recovery identity and configuration IDs.
The top detailed-status slot displays lyrics; the bottom badge reports playback state.

164 targeted checks passed. Both versions ran all 678 embedded tests with identical
614 passes, 51 failures and 13 errors, and no new failing/error test identities.
An additional legacy floating-mask fixture errors in both versions due to a missing
helper in its test namespace; it is documented separately, not counted as passing.
Compilation, full package validation, signatures and interactive publication passed.

See [measurements and manual verification](../docs/performance-v519.md) and the
[lock-screen guide](../docs/windows-lock-screen.md). All reports are directly under
`tests/reports`. The running V518 player was left playing; a relaunch loads V519.

Verified backups precede replacements; older releases remain intact. Playback
function bodies, native color composition, UAC and `play_audio_file.py` are unchanged.
**No literal C:\BAT paths were created, modified or deleted.**
