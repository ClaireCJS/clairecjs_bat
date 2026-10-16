# PAFPlayer V524 release notes

Released October 11, 2026.

## Fixed

- Tray-only startup no longer crashes while creating its hover card after the
  main tray module has configured the process-global `RegisterClassW` ctypes
  signature with a different local `WNDCLASSW` type.
- Ordinary forward shuffle selection now enforces the existing three-hour
  recent-play window using earned history and the launch-visit ledger.

## Short-playlist behavior

When the proposed song is recent, PAFPlayer examines no more than one complete
queue rotation. It selects a distinct, existing, non-recent song when one is
available. If every viable song is recent, it keeps the original proposal so a
small playlist continues playing without a stall or infinite loop. Explicitly
queued Play Next songs are not replaced by the cooldown.
