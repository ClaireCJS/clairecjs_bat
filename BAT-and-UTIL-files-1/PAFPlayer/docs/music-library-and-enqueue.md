# Music library filelist and enqueue

## Ways to queue files in the active playlist

Start a playlist in the official player, then use any of these routes to add
or queue supported audio. They all send playback to the official player; a
tray-only computer does not become a second audio player.

| Where | How to queue |
| --- | --- |
| Command line, saved placement | `PAFPlayer -q FILE [FILE ...]` (`--q` and `--enqueue` are aliases) accepts files or folders. `en.bat` uses this route. It follows the saved placement choice: after the current song by default, or at the playlist end. |
| Force play next | `PAFPlayer -qa FILE [FILE ...]` inserts immediately after the playing song, so these tracks play next. It overrides the saved placement for this request only. |
| Force playlist end | `PAFPlayer -qe FILE [FILE ...]` appends at the end, so these tracks wait for normal playlist traversal. It overrides the saved placement for this request only. |
| Regular expression | `PAFPlayer -q artist.*title`, `PAFPlayer -qa re:PATTERN`, and `PAFPlayer -qe re:PATTERN` search the player library. An argument is a regex when it is **not an existing file or folder** and contains a regex signal such as `.*`; `re:` explicitly marks a regex. Existing paths are treated as paths even if their names contain regex characters. `QQ` opens the whole-library selector. |
| Console playlist | PgUp/PgDn opens the live playlist browser. Select one or several rows and press Enter or Shift+Q to queue them next. `J` or Insert opens the current-playlist song selector; Enter queues there too. |
| Web configuration | In the Playlist queue editor, select rows and choose **Play next** or **Play after current**. The library-search results can also be approved for queueing. The web page accepts dropped audio files and folders, and its file/folder pickers can add them. |
| Desktop windows and tray | Drop files or folders on the official player's artwork window, Floating Lyrics window, or notification-area tray icon. The same queue bridge handles all three. |
| Another computer | Run `PAFPlayer --tray-only HOST:PORT` and drop files or folders on that computer's tray icon, artwork window, or Floating Lyrics window. `en --server HOST:PORT ...` and the remote enqueue API also reach the central player. |

Ordinary `-q` and added-file drops use the saved **Command-line enqueue
placement** choice: **After the current track** by default, or **End of
playlist**. `-qa` and `-qe` override that choice for one request. Console
**queue next** and web **Play next** explicitly schedule the selected tracks
next. A queue change is live; saving changes to the playlist file is a separate
action.

`PAFPlayer --simple FILE` always plays FILE in its own simple process. It does
not hand the file to an already running official instance or claim the official
tray. Use `-q` to send a request to the running player instead.

Drop an audio file or folder onto the web page, artwork window, Floating Lyrics
window, or tray icon to enqueue it. A folder is resolved by the
official player's normal folder scanner. The web page can upload local browser
files when their original paths are hidden; the saved **remote uploads** switch
still controls uploads from another computer. Web uploads retain the existing
100 MiB per-file and 512 MiB managed quota. Native window drops require an
active playlist and depend on Windows delivering `WM_DROPFILES` to that window.
On a tray-only computer, tray-icon, artwork, and Floating Lyrics drops send file
and folder-content hints to the central player. The server resolves them in
its own library; different drive letters are fine, but missing or ambiguous
matches are rejected. This does not transfer audio bytes from the client.

PAFPlayer uses `C:\mp3\lists\everything.m3u` as its default full-library
filelist. Change and save this path in the web configuration's **Security → Full
music library filelist** control. The choice is saved in the existing workflow
settings under `music_library_playlist`; it is used by regex lookup, catalog
search, and the background missing-filelist builder.

`PAFPlayer -q FILE`, `PAFPlayer --q FILE`, and `PAFPlayer --enqueue FILE` all
enqueue into the official active player. `en.bat` uses `--q`. An exact audio file
that already exists on the player computer goes straight to its queue. It does
not need an `everything.m3u` file or a library scan. A missing filelist never
blocks that direct-file case.

By default, enqueue places every requested song immediately after the current
track in the visible playlist, in the order supplied, and plays them next. If
one is already elsewhere in the playlist, its existing row moves there instead
of leaving an apparently missing request at the end. Change **Command-line
enqueue placement** in the web Playlist tab to **End of playlist** to make
ordinary `-q`/`--enqueue` requests append instead; those songs then wait for
normal playlist traversal. The choice is saved as `enqueue_placement` in the
existing workflow settings on the official player. Its factory default is
**After the current track**.

`PAFPlayer -qa FILE` always inserts after the current track; `PAFPlayer -qe
FILE` always appends at the end. Both accept multiple files, regex selectors,
and `--server HOST:PORT`, and neither changes the saved placement preference.
The official player resolves the preference for remote and local requests, so
a tray-only computer uses the server's choice. Explicit flags override it for
one request. Placement affects the running playlist; saving a playlist to disk
still requires the separate save action.

The enqueue receipt reports both the number accepted and the number of new
playlist entries. An existing song can move within the playlist without adding
a new entry. In after-current mode the accepted songs play next even when the
current track was at the end; in end mode they play when normal traversal
reaches their new positions.

Use a pattern containing `.*` or `re:PATTERN` to search the music library. When
the chosen filelist is missing, PAFPlayer warns and checks its index, active
queue, and configured music folders. If those cannot match, it scans audio in
the invoking shell's current folder and its subfolders, then branches outward
into the parent folder's other branches. It repeats for up to four parent
levels, examining at most 25,000 entries. A remote command's folder is used only if the player
computer can access that same path; otherwise the search starts from the player
computer's current folder. If the library root is available, PAFPlayer also
builds a missing master filelist in the background. A search can still fail
when none of these sources contains a match or the bounded scan ends first.
Searching folders may take longer than using a current filelist. Exact existing
audio files enqueue directly without any library lookup.

V623 shows a status line immediately while the official player resolves a
regex. It then lists matching filenames in soft alternating colors, grouped
under each folder once. Color falls back to plain text when the terminal does
not support it. Up to 20 results are queued automatically after the preview.
For 21 or more results, PAFPlayer shows the first 20 and asks for **Y** to
enqueue all, **L** to list every match, or **N**/Enter to cancel. A redirected
or missing interactive stdin cancels a large request without queueing it.
The owner resolves paths once into a one-use preview valid for ten minutes;
the commit rechecks that matched media still exists. Direct file requests
also show a resolving/queueing status line, without an extra preview round
trip when 20 or fewer paths were supplied.

The player resolves enqueue requests and edits the official queue. A client
timeout does not prove the request failed: the owner may complete it after the
client stops waiting. Check the queue before retrying so you do not add the
same tracks twice. The third console HUD detail line briefly shows external
queue changes and controls without exposing track paths.
