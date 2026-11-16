# PAFPlayer V685 — Playlist window lifetime

The playlist status variable now belongs explicitly to the playlist window’s Tk interpreter, even when another PAFPlayer Tk window already exists. The trace records window open, toggle, shutdown, close reason, callback errors and unexpected thread termination.

The previously reported disappearance cannot be attributed to a specific close request from V684 logs, which did not record those reasons. This fix addresses the Tk ownership defect and adds evidence for future diagnosis; it does not claim that defect caused the reported event.

Verification: a Windows Tk lifecycle regression with another Tk root already active, the V684 focused playlist tests, syntax and bundled-source parity checks, and release-copy parity.
