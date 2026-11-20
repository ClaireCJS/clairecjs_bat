# PAFPlayer V742 — Simple playback without startup splash

The five-second startup title is no longer initialized or drawn in simple mode. A simple preview does not consume the once-per-process startup title for a later normal session. Normal playback keeps its existing splash.

Playback-level regression tests reproduce the former failure and verify simple and normal behavior. Existing simple-instance tests and bundle/source parity checks pass. The older V576 web-title test still expects the removed `consoleTitleDropdown` element; V741 has the same failure, independently of this change. No installed copy was modified.
