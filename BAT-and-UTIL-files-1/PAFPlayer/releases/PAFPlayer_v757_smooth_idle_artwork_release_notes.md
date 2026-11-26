# PAFPlayer V757 — smoother idle artwork animation

Position-only dance Configure events no longer schedule image resampling, border suppression, title updates or placement saves. The native window still moves without activating or changing Z-order. Actual user resizing retains the normal rendering path.

Animation targets 60 Hz using monotonic deadlines; callback work is subtracted from the next delay and missed frames are skipped without catch-up bursts. Existing subpixel/time-based motion keeps its speed, bounds, beat reaction and origin restoration. The main dance reuses the existing monitor-watcher snapshot. When not dancing, idle detection polls at 100 ms rather than animation rate.

`art.idle.pacing` diagnostic summaries report measured FPS, longest callback gap, longest callback work and extra-window count every ten seconds while dancing. These measurements are needed to assess residual jitter on the affected display; automated tests do not establish actual compositor smoothness. Restart PAFPlayer to load this release.

Validation includes extracted real Configure/scheduler callbacks, missed-frame pacing, unchanged motion speed across 30/60/120 Hz, monitor-safe bounds, gallery layout and existing beat behavior. An unrelated historical V653 test still expects the removed experimental schema flag; that stale assertion is recorded separately from animation tests.
