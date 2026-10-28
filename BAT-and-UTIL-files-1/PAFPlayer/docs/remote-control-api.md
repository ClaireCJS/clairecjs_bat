# PAFPlayer remote-control API

## V623 enqueue previews and confirmation

Regex requests first send `POST /api/remote-enqueue` with the official owner
`identity`, `selectors`, and `"preview_only": true`. The owner resolves the
library and returns `matches`, `count`, and a one-use `preview_token` without
editing playback. The CLI displays grouped, colored filenames. For more than
20 matches it requires an interactive **Y** before sending a second request
with the same `identity`, `preview_token`, and optional `placement`. Tokens
expire after ten minutes; commit verifies the matched files again. A changed
official owner, expired token, missing file, or declined prompt leaves the
queue untouched. Loopback single-instance IPC uses the same preview/commit
flow. Small direct-file requests continue to use one request.

## V622 enqueue placement

`-q`/`--enqueue` insert after the current song by default, in both the
official player's visible running playlist and its explicit next-play queue.
The Playlist web tab can save **End of playlist** as the ordinary enqueue
behavior. `-qa` and `-qe` force after-current and end placement for one local
or `--server HOST:PORT` request. They do not alter the saved choice. End
placement appends to the running playlist and awaits normal traversal.

The remote enqueue JSON accepts an optional `placement` field with
`"after_current"` or `"end"`. If omitted, the official player applies its
saved setting. The owner still verifies its identity before accepting the
request. The same optional field travels through local single-instance IPC.

## V616 short enqueue and automatic master list

`PAFPlayer -q metallica.*justice` and
`PAFPlayer --enqueue metallica.*justice` mean the same thing. The nonexistent
argument contains `.*`, so the client treats it as a case-insensitive regular
expression. The official player searches full normalized paths in its own
`everything.m3u`, active playlist/queue and library index, then queues every
match. The argument can be unquoted when your shell passes it as one token.
Use `re:PATTERN` or `--regex PATTERN` when the pattern could also look like a
literal filename.

If the configured `everything.m3u` is absent when the official player starts,
PAFPlayer schedules a background walk of its configured music root(s). It
publishes a UTF-8 M3U only after the walk succeeds, never rewrites an existing
master list, and leaves playback running while it scans. While the first scan
is in progress, searches can use the active playlist and existing library
index; a song absent from those sources may require a retry after the new
master list appears. If no music root exists or a folder cannot be read, the
build reports an error and does not publish a misleading partial master list.

## V615 remote enqueue and library search

With `MUSIC_PLAYER=PAFPLAYER`, `en.bat` calls `PAFPlayer --enqueue`. Examples:

```text
en "D:\Music\Artist\Album\Song.flac"
en re:"Girl Tones/.+Blame.*\.flac$"
en --regex "(?i)girl tones.*blame"
en --server musicbox:666 "E:\My Music\Song.flac"
```

The client sends file hints to the **official player**, which resolves them
against files on that machine. A different drive letter is fine. The server
uses the filename, trailing folders and (when the client has the file) size;
it rejects ambiguous names instead of picking one at random. A file available
only on the client cannot be enqueued this way. The `--server` option selects
one player for this invocation; `PAFPLAYER_SERVER` can supply a default. A
`--tray-only HOST:PORT` launch remembers that server in roaming AppData for
later `en` calls on the same computer. A local official player takes priority
when no server is specified. The player must bind its web server to a LAN
address (for example `--web-host=0.0.0.0`) and the client must be able to
reach that port; the default loopback bind accepts only same-computer requests.

Regular expressions search normalized full server paths, case insensitively.
Patterns may be marked with `re:` or `--regex`; recognizable regex syntax is
also detected when the argument is not an existing file. A plain filename is
treated as a file hint. Search sources are `C:\mp3\lists\everything.m3u`,
the current playlist/queue and the existing persistent workflow library
index. The active queue is searchable immediately. Opening a playlist indexes
its tracks and scans a configured music root when one contains them; otherwise
it scans each track folder's parent and subfolders. This runs in the background
with a 25,000 entry scan bound.
If there is no searchable catalog, or a regex finds nothing, the command
prints an error. Very large matches (over 5,000 tracks) are rejected.

The transport is `POST /api/remote-enqueue` with the current official-instance
identity from `GET /api/remote-tray/hello`. The server checks the identity
again when editing its playback queue. The HTTP endpoint uses the existing
private-LAN trust model; it has no account authentication. Do not expose the
web port to the public internet.

V564 provides a small open API intended for a phone/tablet remote or a
homescreen pause widget. No secret or account setup is required. It does not
expose the general `/api/action` queue to remote clients.

## Endpoints

`GET /api/remote/status` returns the same current status snapshot used by the
web controller. A widget can poll this endpoint and use the playback fields to
show whether PAFPlayer is playing or paused.

The following endpoints accept an empty JSON body and queue the corresponding
player action:

```text
POST /api/remote/pause
POST /api/remote/resume
POST /api/remote/toggle-pause
```

`202` means the action was accepted by PAFPlayer; `503` means the player is
temporarily unable to accept it.

## Network safety

The API follows the existing PAFPlayer web-server bind setting. Because this
is intentionally open, use a private LAN/VPN or an HTTPS reverse proxy and do
not expose it directly to the public internet. PAFPlayer does not terminate
TLS or provide authentication.

Example request:

```text
GET http://player-host:666/api/remote/status
```
