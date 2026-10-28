# V558 global responsiveness optimizations

V558 removes avoidable repeated work without changing audio, visualizer quality,
search results, tray choices, or polling intervals.

1. Whole-library query reconciliation now waits 150 ms and abandons superseded
   queries before starting `os.walk`. Rapid typing therefore launches one useful
   filesystem scan rather than overlapping scans for each intermediate prefix.
2. The tray coalesces its repeated registry-setting reads for 500 ms. Explicit
   setting changes invalidate the cache immediately, so Web Config and native
   menu changes still apply at once.
3. Tray mouse movement refreshes the hover-card snapshot at most ten times per
   second. Windows can emit many more mouse messages, but the 0.666-second hover
   timer and displayed information do not require a server snapshot per message.
4. Web Config builds the 200 tray-icon canvas/button elements once per catalog
   version. Its existing status poll now updates selection state rather than
   destroying and redrawing every canvas every three seconds.
5. The server retains one immutable 200-entry tray-icon catalog instead of
   rebuilding 200 dictionaries for every Web Config status response.

These are workload reductions, not a claimed universal startup or FPS multiplier.
Their effect is largest while typing library searches, hovering over the tray,
or leaving Web Config's 200-icon gallery open.
