# PAFPlayer V583 — prepared large-playlist transitions

V583 moves repeatable successor work off the end-of-track boundary without
changing shuffle, cooldown, manual queue, repeat, mutation, pause, seek, stop,
folder-monitor, or single-instance ownership semantics.

The player now retains one signature-checked prepared successor and directly
reuses its duration, tags, ReplayGain choice, silence bounds, and lyrics. Album
art remains in the existing bounded render cache. Rapid requests are latest-
wins; stale, missing, unreadable, or modified files are rejected.

The final 6,000-slot synthetic diagnostic measured successor selection at
0.061 ms median and 0.101 ms p95 over 2,000 transitions on the development machine. A
local WAV preparation probe measured 315.605 ms on the cold synchronous path
and 0.207 ms to validate/take an already prepared result. Those are preparation
measurements, not an audible-gap claim. Live decoder/device startup remains at
the boundary and is now recorded in `transition.decoder-start`.

The Playback page adds a -5000..+10000 ms silence/overlap control. Positive
values deliberately delay the next track. Negative values are saved but not
activated because the existing single-stream renderer cannot safely overlap
tracks; no renderer redesign or “zero lag” claim is included in this release.
