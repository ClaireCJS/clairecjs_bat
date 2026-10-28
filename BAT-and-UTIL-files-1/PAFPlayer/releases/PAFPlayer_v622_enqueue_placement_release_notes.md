# PAFPlayer V622 — enqueue placement

Released October 26, 2026.

- `-q`, `--q`, and `--enqueue` now place requested tracks immediately after the current track in the visible running playlist by default. Multiple requests keep their supplied order. A track already elsewhere in the playlist moves to the requested position; its audio file is never changed.
- The Playlist tab has a saved **Command-line enqueue placement** choice: **After the current track** (factory default) or **End of playlist**. The preference lives in the existing workflow settings on the official player.
- `-qa` forces after-current placement and `-qe` forces end placement for one invocation. Both accept the existing file, regex, and `--server HOST:PORT` forms. Neither rewrites the saved choice.
- In end mode, tracks await normal playlist traversal. In after-current mode, they also enter the explicit next-play queue. The owner validates and applies the choice for both local and remote clients.
- A single-file session can traverse tracks appended with `-qe` after its current song.

Verification: V622 placement tests, related enqueue and workflow tests, and Python syntax checks. The running V621 process must be restarted to load V622. Shuffle's ordinary playback policy may reorder natural end-placement traversal; explicit after-current requests retain play-next priority.
