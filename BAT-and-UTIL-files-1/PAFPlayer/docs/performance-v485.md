# V485 rendering and bass controls

The terminal visualizer still requests 120 FPS by default. To choose a lower
ceiling, use the existing `--visualizer-target-fps=60` or
`--visualizer-target-fps=90` option. The adaptive governor may reduce the rate
under load. F5 shows measured callback FPS; it does not measure display refresh.
No visual preferences are changed by this release.

Artwork-colored twin-DRCS frames with row-independent processors, static
background detail, and single-byte DRCS glyphs use vectorized cell composition.
Semantic transport now carries foreground, background and glyph together.
Background and bar colors, rounding, partial edges, top blanks and truncation
match the retained renderer. Unicode/fenced cells, monochrome diagnostics,
RGB capture, unsupported geometry and brightness feedback use the existing
renderer. Dimension, artwork and DRCS-bank changes invalidate cached output.
Caches retain their identity sources and have fixed entry limits.

Windows x64 has a small bundled native encoder with no external runtime DLL
requirements. Its checked source is `tests/PAFPlayer_v485_encoder.c`; it was
built with MSVC x64 `/O2 /Oi /GS- /LD /link /NOENTRY /NODEFAULTLIB /MACHINE:X64`.
The Python file embeds and SHA-256 verifies the binary, then materializes it
under `%TEMP%/PAFPlayer-native/artwork-<sha256>.dll`. Existing matching files are
reused; differing files are preserved under the numbered-name collision rule.
The Python encoder remains available when native loading is unavailable.
No executable download occurs at runtime and no global packages are changed.

Frame scheduling uses QueryPerformanceCounter through `time.perf_counter` on
the normal playback path. Audio position and external-media timestamps remain
in their existing clock domain. Injected monotonic clocks still drive tests.

## Bass reduction while locked

Enabling/disabling lock-only bass reduction or editing its amount while
unlocked saves the preference immediately without interrupting playback.
Changing the boost amount while boost is disabled behaves the same way.
The decoder restarts only when the effective bass shelf changes. Lock/unlock
uses the same effective-dB comparison, including clamped combinations of boost
and reduction. Audible changes use the short interactive startup buffer.

[release history](PAFPlayer_changelog.md)
