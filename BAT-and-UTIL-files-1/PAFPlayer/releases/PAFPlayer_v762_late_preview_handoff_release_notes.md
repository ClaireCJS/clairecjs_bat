# PAFPlayer V762 — pause peers at the audible handoff

Simple previews register during setup without claiming audio focus. The buffered renderer starts in hold-for-handoff mode and primes silently while other players continue. Once primed, the preview acquires acknowledged pauses and immediately releases its prepared output. The FFplay fallback acquires focus immediately before process launch, after command and environment preparation.

A failed silent preparation stops its renderer and leaves peer focus untouched until a fallback is ready. Focus/output-start failures stop the held renderer and propagate through normal cleanup, without launching a competing decoder. Existing pause ownership and originally paused/stopped players remain protected. Registering early preserves priority for overlapping silent startups; startup pause latches are refreshed after focus waiting so a previously held preview can actually start.

33 focused tests passed, including the actual playback routine with simulated renderers: creation/priming/claim/output ordering, FFplay timing, preparation fallback, failed focus/output starts, stale startup pause latch, peer acknowledgement and all prior pause/startup ownership regressions. No live player was paused or interrupted for testing.
