# PAFPlayer V766 — Lock-screen clock heartbeat

## Fix

The local lock-screen endpoint extrapolates the most recent playback clock anchor between requests. Previously the host refreshed that anchor only when a browser was connected or Discord was configured, so an offline browser/client state eventually became stale and the displayed clock stopped advancing.

PAFPlayer now publishes a compact playback-clock update once per second when there is no active web client. This refresh includes current lyric timing and track position without serializing the full web status or requesting timeline data across the network. Discord keeps its faster lightweight clock cadence when enabled.

## Verification

The main runnable and this release copy pass Python syntax compilation. No live Windows lock-screen session was started during this change.
