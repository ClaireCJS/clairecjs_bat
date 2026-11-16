# PAFPlayer V631 — queue status and test triage

Released October 30, 2026.

- Web and remote queue reads use a cached missing-file snapshot. One daemon worker refreshes it after membership changes and every 10 seconds. Requests do not wait for file checks on a slow drive.
- The playlist source cache stores parsed path candidates and rechecks file existence, so a missing file that reappears is reflected without editing the `.m3u` file.
- Queue edits retain known missing flags and avoid statting every entry under the playback queue lock. Queue membership and transport remain live; only advisory file status is cached.
- The embedded suite still executes all tests. Its 57 exact V630 baseline failures are marked expected and printed as such; a newly passing one or any new failure fails the audited run. `--unit-tests-raw` runs without expected-failure marks. The full discrepancy list and migration guidance are in `docs/testing.md` and `src/PAFPlayer_test_triage.py`.
- The first queue response after a membership change can briefly omit missing-file flags until the worker publishes. On a busy or sleeping drive, that delay may exceed 10 seconds; subsequent reads remain responsive.

Verification: focused queue-cache and test-triage tests, relevant queue/IPC regressions, the audited embedded suite, Python syntax checks, and single-file bundle/source parity. The 18 behavior/fixture discrepancies are still under review; expected-failure status is not proof they are harmless. Live Windows shell and audio-device behavior was not tested.
