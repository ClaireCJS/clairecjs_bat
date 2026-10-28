# PAFPlayer V615 — remote library enqueue

`en` now queues into the running official PAFPlayer instance, locally or from
a tray-only computer. `PAFPlayer --enqueue [--server HOST:PORT] FILE ...` is
the direct command. A tray-only launch remembers its last server in roaming
AppData. Client drive letters are hints; the player resolves names, trailing
folder names, and optional file size against its own files. Ambiguous or
missing matches produce errors.

Regular expressions use `re:PATTERN`, `--regex PATTERN`, or recognized regex
syntax. Searches include `everything.m3u`, active playlist/queue entries and
a persistent workflow index. Loading a playlist indexes its entries and scans
the configured music root, or nearby folders, in the background. No catalog
or no regex matches is an error.
Requests remain bound to the verified official instance identity; only that
instance edits the playback queue.

The catalog scan is bounded at 25,000 entries and enqueue matches at 5,000.
Remote enqueue uses the existing private-LAN web port without additional
authentication. The player computer must have the selected audio files; the
client's file path alone does not transfer media.
