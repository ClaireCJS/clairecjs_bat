# PAFPlayer V761 — faster simple-preview startup

Metadata and edge-silence analysis are cached across processes under runtime/cache/track-analysis. Keys include file identity, size, modification/creation timestamps, analysis settings and tool signatures. Changed media/settings invalidate the cache; failed scans are not persisted. ReplayGain metadata, channel layout and exact trim bounds continue through the normal parsing paths. Corrupt/unwritable caches fall back to analysis.

Isolated audio workers reuse compiled player code under runtime/cache/worker-code, keyed by the complete source contents and Python bytecode version. The real script/module identity, command/status protocol and isolated audio process are preserved. On a cold code cache, compilation runs in a hidden background process at below-normal priority and the current preview uses ordinary source startup. Cache records are immutable and published after writing; no old entries are overwritten or deleted.

Measured with the installed runtime on this computer, without producing audio: worker loading was 1.316 seconds from source versus 0.505 seconds with warm compiled code. One real track's metadata/silence analysis was 0.313 seconds cold versus 0.048 seconds cached, with identical duration and trim bounds. The first cache request used ordinary source startup (1.546 seconds while background preparation ran). These are component timings, not end-to-end playback measurements; first-use analysis and file I/O still cost time.

Validation covers persistence after memory-cache resets, file/parameter invalidation, failure/corruption fallbacks, asynchronous worker-code creation, module identity, immutable warm reuse, preview pause ownership/startup, ReplayGain metadata reuse and simple-mode rendering.
