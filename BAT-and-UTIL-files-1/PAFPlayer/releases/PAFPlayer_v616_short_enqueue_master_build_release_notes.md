# PAFPlayer V616 — short enqueue and automatic master list

`-q` is an alias for `--enqueue`. For example,
`PAFPlayer -q metallica.*justice` recognizes the nonexistent argument's `.*`
as regular-expression syntax and queues all matching files from the official
player's catalog, locally or through the remembered tray-only server.

If `everything.m3u` is missing, the official player builds it in the
background from configured music roots. It writes a complete UTF-8 M3U to a
staging file, then publishes it without replacing an existing list. Playback
does not wait for the scan. An unavailable or unreadable root leaves the
master list absent and records a workflow error. Existing library and active
playlist entries remain searchable during the build.

Tests cover both CLI spellings, unquoted regex detection and matching,
background scheduling, complete-list publication, existing-list preservation,
and the no-root error.
