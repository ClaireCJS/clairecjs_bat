# PAFPlayer V752 — quiet seek-related HTTP disconnects

The RAM-audio server previously caught only broken pipes and connection resets during body streaming. Decoder restarts can also close sockets during request reads, headers and final flushes; socketserver's default handle_error then printed a traceback into the inline UI.

A server-level handler now contains those failures across the full request lifecycle. Expected connection abort/reset/broken-pipe events go to the existing trace log, unexpected exceptions retain full diagnostics in the error log, and recent request outcomes are bounded in memory. Logger failures cannot escape into socketserver's stderr handler. The main web server also contains exceptions that occur outside its per-request wrapper.

Focused verification injects aborted headers, final-flush resets and unexpected handler failures through actual loopback HTTP request threads, asserts empty stderr, checks diagnostics and verifies subsequent range requests still succeed. Existing RAM-audio and inline playback regressions are retained.
