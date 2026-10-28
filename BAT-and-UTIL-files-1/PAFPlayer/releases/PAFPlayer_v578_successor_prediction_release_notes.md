# PAFPlayer V578 — playlist successor prediction

Released October 19, 2026.

## Changes

- The background preparation worker predicts the next track after shuffle
  rotation and recent-play cooldown. It follows manually queued tracks, resume
  successors, and forward visit history when available.
- The worker performs file and history checks after the current decoder starts.
  Current-track startup no longer scans for its playlist neighbor on the
  playback owner thread.
- The predicted track uses V577's shared metadata, ReplayGain, silence-bound,
  and console-cover preparation caches.

## Validation and limits

Focused tests cover shuffle rotation, cooldown replacement, manual and resume
priority, forward history, and ordinary queue order. Random track selection,
late queue edits, and short songs can still invalidate a prefetch hint. V578
does not provide a continuous PCM stream between tracks, and live timing on a
6,000-track playlist has not been measured. The zero-lag transition TODO stays
open. The install survey remains deferred for a future prompt.
