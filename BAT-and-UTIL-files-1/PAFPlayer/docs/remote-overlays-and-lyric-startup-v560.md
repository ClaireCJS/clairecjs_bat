# V560 transport HUD and remote overlays

## Transport-state color

The word `Play:` in the console HUD reflects transport state without changing
the path color:

- playing: the established green;
- paused: bright yellow;
- stopped: bright red.

The stopped state remains visible while the player is stopped and clears when
playback resumes.

## First-lyric startup work

Before launching the audio decoder, PAFPlayer now prepares the first three
non-empty lyric lines using the active lyric style and Emojimaxx settings. This
populates phrase-substitution, Unicode cell-width, double-height compensation,
and wrapping caches before the audio clock starts. The first displayed lyric
therefore performs ordinary painting rather than cold semantic/layout setup.

## Remote tray presentation

In `PAFPlayer --tray-only HOST:PORT` mode:

- Ctrl+Alt+F toggles floating lyrics on the tray computer.
- Ctrl+Alt+A toggles the album-art popup on the tray computer.
- The Shift forms remain aliases for those same local toggles.
- A newly enabled overlay causes its presentation worker to start immediately.

The official player publishes a monotonically increasing lyric-timeline
revision. The remote client downloads the complete timeline only when that
revision changes (normally once per track or lyric reload). Artwork is likewise
downloaded only when its artwork generation changes.

While either overlay is enabled, the client performs a reconciliation heartbeat
once per second. Each status contains the sampled playback position, playback
speed, play/pause state, and the server wall-clock epoch for that sample. The
client also estimates server/client clock offset from the request round trip.
Floating lyrics advance locally from those anchors at display-frame cadence;
the next heartbeat corrects any accumulated clock or transport drift. Pausing,
stopping, seeking, changing speed, changing tracks, and server-owner replacement
are therefore reconciled without requiring cue-by-cue network messages.
