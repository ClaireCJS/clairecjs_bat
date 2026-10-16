# PAFPlayer V534 — simulated playlist run

V534 adds `--simulated-playlist-run PLAYLIST`. It loads the requested playlist,
builds the ordinary history-weighted shuffle, and drives the same rotating queue
and bounded cooldown-selection core used by live playback for 180 seconds without
opening an audio device.

The run keeps simulated visits in memory, so it does not scrobble, earn plays, or
persist synthetic launch history. Its timestamped JSON report in `tests\reports`
records throughput, cooldown replacements, unavoidable all-recent fallbacks,
avoidable violations, immediate path and Artist+Song repeats, minimum repeat gaps,
and the largest bounded scan. Any avoidable cooldown violation or immediate repeat
makes the command fail with a nonzero exit status.

`--simulated-playlist-seconds=N` is available for short automated diagnostics.

The first simulator run exposed a path-only launch-ledger gap. V534 consequently
persists a second, normalized Artist+Song launch identity and consults it during
selection. Different album paths for the same recording now share the immediate
cooldown even when the listener skips before either path earns play history.
