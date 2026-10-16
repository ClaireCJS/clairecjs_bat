# PAFPlayer V537 — durable playlist resume

Released October 13, 2026.

V537 fixes playlist resume after an interrupted run. The selected track is now
bookmarked before decoder startup, and its source-file playhead is refreshed in
the registry approximately every two seconds while playback continues.

Previously, the ordinary transition path cleared the prior bookmark and only a
specific `stopped` result saved a replacement. A console Ctrl+C/Ctrl+Break raised
`KeyboardInterrupt` out of the track player, bypassed that branch, and left no
usable bookmark; the following launch therefore selected a different shuffled
track. Live checkpoints make that shutdown path—and abrupt termination shortly
after the latest checkpoint—resume the same song near the interrupted position.

Checkpoint failures are diagnostic-only and cannot stop or disturb audio.
