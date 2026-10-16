# PAFPlayer V493 — track handoff profiling

V492 live handoffs still took about 6–7 seconds to audio start. V493 adds timestamped trace points after settings persistence, resume clearing, shuffle rotation, and successor selection, so the blocking stage can be isolated on the next live handoff. Floating Lyrics fixes from V492 remain included.

This is a diagnostic release pending the measured fix.
