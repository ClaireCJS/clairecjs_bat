# PAFPlayer V655 — Idle Behavior motion

Released November 11, 2026.

## What changed

- All artwork-idle controls now live in one **Idle Behavior** tab, positioned in
  the same order as its settings section.
- Added persistent **Try to go back to where you started** and **Wander pattern**
  settings.
- Patterns are Smooth random roam, Edge bounce, Orbit, Figure eight, and
  Speed bump — beat arc.
- Animation now runs at about 30 FPS with fractional, elapsed-time movement,
  replacing 140 ms whole-pixel jumps.
- Random and edge patterns always choose a meaningful next destination. The
  speed-bump path reverses mathematically at its ends, fixing boundary stalls.
- The main cover and related-art gallery use the same motion implementation.

## Beat behavior

**Dance to music uses actual beat/onset energy already computed for progress-bar
coloration.** It does not perform a second audio analysis. The timestamped pulse
changes travel speed; stale pulses become zero energy. A small baseline speed is
retained so quiet passages no longer freeze the artwork indefinitely.

## Verification

- `python -m unittest PAFPlayer.V655IdleBehaviorMotionTests -v`
- `python -m py_compile PAFPlayer.py`
- source checks for the new web hosts, settings, action handlers, and shared
  motion function

## Remaining limitation

Window placement is integer-pixel at the final Win32/Tk boundary, so very small
ranges can still repeat a pixel across adjacent 30 FPS frames. Motion state is
fractional, so it continues advancing rather than becoming stuck.
