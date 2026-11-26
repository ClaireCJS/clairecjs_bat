# PAFPlayer V753 — normal-height post-playback output

Completion, interruption and cleanup arm a text-output guard that prefixes every output row with BIG_OFF (ESC # 5). The guard covers stdout/stderr prints, background messages using those streams, console payloads, newline/CRLF/carriage-return boundaries, blank rows and the next prompt row. The optional second completion row also receives an explicit reset after moving to it. No screen clear is added.

Starting the next track removes the output proxy and re-enables normal double-height karaoke rendering. Stream attributes and flushing are forwarded, and partial writes are completed without losing output.

Verification covers multiline and blank-row resets, stdout/stderr and fragmented prints, CRLF, short writes, console output, next-track re-enablement and existing simple-mode interrupt/playback behavior.
