# PAFPlayer V579 — isolate playback tests from the official player

Released October 19, 2026.

## Incident and cause

The October 19 embedded test run invoked `main()` with temporary playlists
while the official PAFPlayer instance was playing. Normal single-instance
behavior forwarded four test playlist loads to the official instance between
10:42 and 10:44. The final load contained one track. After the temporary file
was removed, the old player retained that one-track in-memory queue, so Next
kept replaying Girl Tones, “Blame.” The real 174-track playlist on disk was not
overwritten; a later player process loaded it and advanced to Niis.

## Fix

- Embedded `--unit-tests` mark their in-process `main()` calls as test calls.
  Standalone `unittest` methods and in-process pytest calls receive the same
  isolation.
- A test call runs without acquiring the official-instance mutex or forwarding
  to its IPC server. It has no tray icon and cannot start the ownership-claim
  watcher. Normal command-line launches retain existing single-instance
  behavior.
- The one-track regression test asserts that no mutex acquisition or playlist
  forwarding occurs while exercising local playlist behavior.

## Validation and limits

The focused one-track regression passed while the real official player was
running. A subsequent standalone test revealed the need for the `unittest`
runner-frame guard and briefly loaded a two-track temporary queue; the normal
single-instance handoff restored the original 174-track queue at 11:26:32.
Both standalone playlist tests then passed with acquisition and forwarding
blocked, and the trace showed no further `queue.edit`. Selected
playlist, tray, workflow, and V577–V578 regressions are recorded in the task
report. This guard covers the embedded runner, standalone `unittest` methods,
and in-process pytest calls. Other standalone scripts that deliberately call
`main()` remain normal launches unless they provide their own isolation.
