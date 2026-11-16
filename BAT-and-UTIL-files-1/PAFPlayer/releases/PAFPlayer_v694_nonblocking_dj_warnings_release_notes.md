# V694 — Nonblocking DJ warnings

Track startup uses cached DJ warnings while a background worker refreshes the warning and sleep state. Credit changes are reflected immediately. A stale warning may remain briefly if refresh fails.

Verified with a held DJ lock and focused DJ regression tests. Live playback timing still requires verification.
