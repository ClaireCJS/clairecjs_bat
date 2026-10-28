# PAFPlayer V571 — source-compared release history

V571 replaces 241 source-only changelog entries that previously repeated archive
filenames. It describes the changed code and, where present, version-specific
regression checks. The V275 entry, for example, now records its 120 Hz deadline
wait, synchronized profiler totals, Escape-only report dismissal, and benchmark
progress refresh.

The audit compared 239 archived source files with the nearest earlier full
snapshot. V13 is the earliest surviving full snapshot, so its entry describes
what that source contains without claiming an introduction date. The surviving
V472 file is an integration script, not a full player snapshot; its entry says
what the script changes. Entries with a large predecessor gap or only
release-identity changes say so. Historical behavior was not run or validated
by this documentation release.

Supporting evidence and curated descriptions are in `tests/reports`:
`v571_release_history_diff_evidence.json` and `v571_curated_*.tsv`. The
comparison tool is `tests/release_history_audit.py`. No playback code or
settings behavior changes in V571. The executable remains based on the V569
behavior build, with its documentation version advanced to V571.
