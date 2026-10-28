# Playlist controls during playback

## V627 startup resume display

When PAFPlayer restores a saved song in a playlist, startup names both files
on separate lines: **Resuming playlist:** shows the playlist filename, and
**Resuming song:** shows the audio filename and saved time. The two filenames
start in the same console column and use terminal italics where supported.

## V624 live playlist browser

PgUp/PgDn keeps its visible page current when another process inserts songs
into the active queue. Focus and selected rows follow the same tracks across
that refresh. Space selects a row; Shift+Up/Down extends selection. **Delete**
removes the selected tracks from the active playlist without interrupting the
current audio. The eight-second **Save deletion to {playlist filename}?** prompt
defaults to Yes; **N** keeps the change in this session. **Ctrl+Z** restores the
last browser deletion, including a saved playlist file if nobody edited that
file afterward. **Ctrl+C** copies selected absolute file paths. With a selection
active, Up/Down moves the selected rows one place in this session; this does
not rewrite the playlist file. A queued-only track can be removed even when it
has no row in the original playlist file. The current song keeps playing.

## V622 enqueue placement

`-q` and `--enqueue` add tracks immediately after the playing song by default,
both in the visible playlist and the next-play order. The Playlist tab's
**Command-line enqueue placement** dropdown can switch ordinary enqueue to
**End of playlist**. `-qa` and `-qe` force after-current and end placement for
one request without changing that saved choice. See [music library and
enqueue](music-library-and-enqueue.md) for remote and regex usage.

## V609 learned-song rules

The learned-song shortcut writes its rule to the track folder's `attrib.lst`.
For numbered tracks it uses a separator-aware prefix such as `^05[ _-]` or
`^4[ _-]01[ _-]`, rather than ending the selector in `.*`. The generator still
checks sibling audio files and uses a more specific title or filename when a
prefix would mark another track. A final writer check refuses any generated
selector ending in `.*` before creating or changing `attrib.lst`. Existing
hand-written rules are left as they are.

## V600 Delete, save, and undo

Pressing **Delete** immediately removes the current track from the active
playlist queue and visit history. The audio file stays on disk, and the song
continues playing without restarting. **Next** followed by **Previous** will
not return to that removed song. If it was the final playlist member, the next
transition ends the playlist instead of replaying the removed file.

After removal, the console asks **Save deletion to {playlist filename}?**
**Enter** or **Y** saves it to the playlist file. Doing nothing for eight
seconds also selects **Yes**. **N** keeps the removal for this running session
but leaves the playlist file unchanged. **Esc** or **Ctrl+Z** at the prompt
undoes the removal. Playback and the console visualizer continue during the
countdown.

After the prompt, **Ctrl+Z** restores the most recent playlist deletion,
including the saved playlist file when applicable. A later setting change takes
the next Ctrl+Z first. A newer playlist edit supersedes this one-step deletion
undo. If the playlist file was edited elsewhere after the deletion, PAFPlayer
refuses to overwrite those newer edits. Each playlist-file replacement first
creates and verifies a sibling replacement backup. The confirmed web removal
and the learned-song **R** shortcut still save immediately.

## V598 accurate Last play cells

The Playlist browser resolves Last play dates in a background worker so opening
or repainting it never waits on SQLite. A cached **Never** is now rechecked
after any newly earned local playback record. This prevents rows that were
drawn before a song finished earning history from continuing to report Never;
they briefly show loading dots and then their real date.

## Song selectors

`J` (and `Insert`) opens the song selector restricted to members of the current
playlist. `QQ`—press Q for the command menu, then Q again—opens the exact same
selector over PAFPlayer's complete known catalog: `everything.m3u`, its fallback
song list, and songs found by live library reconciliation. Enter queues the
focused song next, Ctrl+Space builds a multi-selection, and Shift+Enter jumps.

## Playlist resume bookmarks

V612 adds `PAFPlayer resume` for a restart after a crash or reboot. It reads the
last saved playlist from the existing global resume bookmark and launches that
playlist through the normal player and single-instance path. The saved song and
playhead are restored by the ordinary playlist resume logic; the live checkpoint
is normally at most about two seconds behind playback. No playlist filename is
needed in `autoexec.bat`. A second normal launch still hands the playlist request
to the official instance. An existing V611 or older bookmark has no playlist
path, so launch the playlist by name once after upgrading to record it. If the
saved playlist is missing or has no usable entries, `resume` explains the problem
and exits without starting another player. Running PAFPlayer with no arguments
shows a large blinking resume hint at the end of help when that saved playlist
is usable. Blink and double-height rendering depend on terminal support.

V537 keeps the active playlist bookmark live while audio is playing. PAFPlayer
writes the selected track before decoder startup, then refreshes its source-file
playhead approximately every two seconds. Console interrupts such as Ctrl+C and
Ctrl+Break therefore no longer bypass the only bookmark-saving path; a relaunch
returns to the interrupted song, normally within about two seconds of where it
stopped. The checkpoint is deliberately best-effort and never interrupts audio
if registry persistence itself fails.

V535 keeps ordinary mid-song resume positions unchanged. If a saved position is
extremely close to the end (within the smaller of five seconds or two percent of
the track), PAFPlayer resumes fifteen seconds before the end instead of rewinding
to the beginning.

Bookmarks also store the next track in the active queue. If the bookmarked audio
file is gone on a later launch, PAFPlayer starts with that saved successor when it
is still in the playlist. For an older bookmark without successor information, or
when that successor is also gone, it starts with the first remaining playlist
entry rather than choosing a random entry.

The same uninterrupted current-song behavior applies while paused and to the
confirmed web playlist action. Delete's save question and Ctrl+Z behavior are
described above.

## Shuffle recent-play cooldown

V524 applies a three-hour cooldown at ordinary forward shuffle selection time.
The check combines earned play history with the separate launch-visit ledger, so
a song sampled and skipped moments ago is still treated as recent. If the
proposed slot is recent, PAFPlayer scans at most one complete queue rotation for
an existing, distinct, non-recent song.

The policy adapts to small playlists by availability rather than by an arbitrary
minimum playlist length. When every viable alternative is recent, PAFPlayer
keeps the originally proposed slot and advances normally; it never waits,
loops forever, or exits merely to satisfy the cooldown. Explicit `INS`/Play Next
requests bypass this automatic substitution because the listener chose them.

## Simulated playlist run

V534 adds an audio-free shuffle stress test:

```text
PAFPlayer.py --simulated-playlist-run C:\mp3\lists\favorites.m3u
```

The command builds the same history-weighted queue and exercises the same bounded
forward cooldown-selection core used by live playback for three wall-clock minutes.
It never opens an audio device, scrobbles, earns plays, or persists its simulated
launch visits. Progress appears every ten seconds. A timestamped JSON report is
written to `tests\reports` with transition throughput, avoidable cooldown
violations, forced fallbacks when every track is recent, immediate path and
Artist+Song repeats, and minimum repeat gaps.

For a short diagnostic or automated test, add
`--simulated-playlist-seconds=N`. This changes only the simulator duration; the
ordinary command always defaults to 180 seconds.

The same release also extends the launch-visit cooldown ledger from literal paths
to normalized Artist+Song identities. Sampling one album copy therefore blocks a
second path for the same recording immediately, even before the first copy has
played long enough to earn ordinary listening history.

## Saved shuffle lifetime

The history-weighted shuffle queue is reused across launches until either its
source playlist changes or its saved build age reaches the configured lifetime.
V535 exposed that lifetime as **Fresh shuffle after** in Web Config's Playback
section. It accepts 0 through 168 hours in quarter-hour steps; `0` means rebuild
on every launch. **The current factory default is 72 hours** (changed in V584);
saved choices still take precedence. Queue rotation does not reset the original
build time. This lifetime applies only in Shuffle by history mode.
