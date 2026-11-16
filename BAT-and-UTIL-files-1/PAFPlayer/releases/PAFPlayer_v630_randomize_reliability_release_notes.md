# PAFPlayer V630 — randomize and error recovery reliability

Released October 29, 2026.

- Randomize requests are admitted to the playback action queue before the live shuffle state changes. A rejected request leaves the current order and mode alone.
- The background history worker preserves an accepted live random order when its playlist slots still match. Duplicate entries count as separate slots; changed membership triggers a fresh order.
- Official-instance playlist handoff preserves repeated file entries as separate slots. Regex and standalone target lists retain their existing deduplication behavior.
- Combined playlist-load and randomize handoffs validate their request and randomize bridge before queue mutation. If the load succeeds but randomization subsequently fails, the reply explicitly reports partial success and the command prints a warning. The loaded playlist is not silently described as rejected.
- Error alerts rearm after a track is confirmed healthy. If that track later fails with the same signature during the same run, the user can receive a new alert.
- Shell notification or alert-thread startup failure no longer interrupts playlist recovery.
- The bundled Windows media module now matches its editable source, restoring its official-owner guard and Chrome card reassertion behavior in the single-file player.
- These changes do not alter saved shuffle preferences or the saved history cache.

Verification: seven V630 regressions, 14 V629 randomize/error regressions, 42 relevant existing IPC, queue, playlist, and Windows media tests, Python compilation, and bundle/source parity. A real Windows notification-area and audio-device smoke test has not been performed for this release.
