# PAFPlayer V767 — Client-local lock-screen clock

## Changes

- Remote tray clients now reconcile their state with the master every five seconds instead of once per second.
- Each client retains the received lyric timeline and timestamped playback anchor in memory. Its local lock-screen endpoint extrapolates the clock and selects timed lyrics on each local request; it does not contact the master to render each second.
- Track/timeline revision changes still trigger an immediate timeline refresh during reconciliation. Master heartbeats remain local state updates and do not poll the master.

With three clients, normal status traffic drops from roughly three master requests per second to fewer than one per second total, excluding a second request when a client detects a new lyric timeline.

## Verification

The single-file runnable and its embedded remote-tray module are syntax and byte-parity checked. No live multi-computer lock-screen session was run.
