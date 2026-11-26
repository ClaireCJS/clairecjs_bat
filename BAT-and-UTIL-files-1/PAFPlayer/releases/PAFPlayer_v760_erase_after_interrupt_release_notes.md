# PAFPlayer V760 — erase leftover display after Ctrl+C

The main Ctrl+C handler now prints ANSI erase-to-end-of-screen (`ESC[J`) immediately after `Playback stopped.` and flushes the message. Remaining karaoke/progress content beneath it is erased without adding a full-screen clear, cursor-home or terminal-reset sequence.

Verified by executing the actual interrupt handler body with cleanup side effects mocked and capturing the output order. Seven existing simple-interrupt/startup-splash regressions also pass. No live player was interrupted for testing.
