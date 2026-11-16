# PAFPlayer V635 — asynchronous resume checkpoints

November 1, 2026

- The live playlist resume position is still checkpointed at the existing
  two-second cadence, but its successor lookup and two Windows Registry writes
  now run on a single background worker rather than inside a visualizer frame.
- If a write takes longer than the checkpoint interval, pending positions are
  coalesced so only the newest unsaved playhead is written next.
- The initial bookmark is saved before playback begins. At track handoff,
  PAFPlayer waits for the prior track's pending write before clearing or
  replacing its bookmark. Normal exit allows a bounded worker drain.
- No visualizer mode, playback control, saved setting, or audio buffering
  behavior changed.

The V634 live player was observed with SIXEL disabled. Its ordinary console
visualizer painted about 36–54 frames per second while targeting 73–120;
terminal transport took roughly 3–8 ms per frame. This release removes one
plausible two-second source of stalls, but the reported one-second pauses still
need a live V635 test. A separate process or buffered frames have not been
added because they would not remove Windows Terminal's output bottleneck and
could add visual delay. An abnormal termination may lose the latest position
that has not yet reached the Registry.

Focused tests cover nonblocking submission, coalescing, and playlist handoff
wiring. Python syntax and relevant existing tests were checked separately.
