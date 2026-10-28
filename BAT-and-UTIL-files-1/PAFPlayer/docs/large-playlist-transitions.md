# Large-playlist transitions

V583 prepares the predicted successor while the current track plays. The
prediction retains manual-queue precedence, resume/history order, shuffle
rotation and cooldown behavior. Repeat-track stays inside the current decoder;
repeat-folder and normal playlist advancement use their established selectors.

Only safe, repeatable work is prepared: duration and tags, ReplayGain choice,
edge-silence bounds, lyrics, console artwork, playlist-history filename lookup,
and a bounded 256 KiB file read. A single latest-wins worker retains at most one
pending request and one completed result. Generation changes discard old work;
the consumer also verifies path, size, and modification time.

Trace events:

- `transition.successor-selected`: playlist successor selection time.
- `transition.prepare-consumed`: whether prepared data was used, synchronous
  preparation time, and the background phase timings.
- `transition.decoder-start`: decoder/open time, total post-EOF handoff time,
  measured silence, and whether preparation was ready before EOF.

Run `python tests/benchmark_v583_large_playlist.py` for the deterministic
6,000-slot selection diagnostic. A live playback trace is still required to
measure a particular machine's decoder/device startup and audible gap.

The Playback web-config slider **Silence / overlap between tracks** saves
-5000 through +10000 ms. Zero requests immediate handoff. Positive values add
silence. Negative values are retained as a future overlap request but are not
applied in V583: safe overlap requires mixing two live renderer streams, which
the current measurements did not justify redesigning.
