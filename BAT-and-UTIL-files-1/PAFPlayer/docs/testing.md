# PAFPlayer regression testing

## V631 embedded suite audit

`PAFPlayer.py --unit-tests` runs every embedded test. It marks the 57 exact
failures observed in the V630 full-suite baseline as **expected failures**:
39 historical source or layout assertions and 18 behavior or fixture
discrepancies still requiring reassessment. The names are recorded in
`src/PAFPlayer_test_triage.py`; the unmodified baseline output is retained in
`tests/reports/v630-full-suite-baseline-20261030.txt`. An unexpected new failure
or a newly passing expected failure makes the audited run fail, prompting a
review of the list. Nothing is skipped.

`PAFPlayer.py --unit-tests-raw` runs the same embedded suite without expected
failure marks. Use it when investigating or repairing a baseline discrepancy.
The command exits nonzero while any of those discrepancies remains.

The 18 behavior/fixture items are not certified as obsolete. They include a
Windows SQLite cleanup lock, FFplay seek-command count, console metadata
alignment, frequency-warp mapping, old web defaults, artwork extraction,
playlist history/cache behavior, and the V265 hard-coded version check. Each
needs a modern contract and a focused test before its expected-failure mark
can be removed. The other 39 generally inspect old source strings, HTML
structure, or layout details; a passing current behavior test should replace
each brittle assertion during review.

New focused tests live in `tests/` and run with Python's unittest discovery.
The V631 queue-status tests check nonblocking first reads, cached repeat reads,
membership invalidation, file recovery without playlist edits, and queue edit
behavior while the audio lock is held.

An expected-failure result is a visible record of unfinished test migration.
It does not prove the affected behavior is correct. Real Windows notification,
lock-screen, and audio timing still need device tests.
