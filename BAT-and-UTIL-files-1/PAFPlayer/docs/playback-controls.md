## V626 whole-file memory playback

On Windows, PAFPlayer can read a track completely into RAM and close the
original file before the decoder starts. You can then rename or delete that
file during playback if no other program holds it open. The old 64 MiB cutoff
has been removed. Before buffering, PAFPlayer checks free physical, commit,
and virtual memory and keeps at least 1 GiB or one eighth of installed RAM
available as a reserve, whichever is larger. If there is not enough headroom,
or the read fails, playback uses the original disk file. This decision is
per track; a computer with ample RAM can buffer much larger files.

## V609 Emojimaxx curation

Emojimaxx leaves `product` as ordinary lyric text instead of replacing it with
the mathematical product sign. The Whip mapping remains `𓀓𓀝`; whether those
glyphs render correctly on the physical remote tray computer still needs a
visual check there.

## V601 responsive global seeking

Ctrl+Alt+Left and Ctrl+Alt+Right work while another window has focus. Each
physical press seeks five seconds backward or forward. Rapid taps, including
quick direction changes, now stay in order and are played as separate jumps.
Holding an arrow starts repeating after 250 ms and repeats about every 85 ms.
The key sampler checks every 5 ms; a press and release that both occur between
samples can still be missed.

With the Windows buffered WaveOut output, a seek now reuses the active audio
worker. It starts a new FFmpeg decoder and short-preroll WaveOut output inside
that worker, keeps the old stream playing until the new output starts, and
retires the old output afterward. This avoids loading a second copy of the
large PAFPlayer Python program for each tap. Seek output uses 1,024-frame
blocks and at most 20 ms of initial preroll, then returns to 4,096-frame
blocks for sustained playback. Initial track launches keep their saved
buffer setting. If this in-worker handoff fails, PAFPlayer tries the previous
replacement-worker path. The legacy FFplay output still restarts its process.
Web and console seek bursts retain their cumulative behavior.

Six muted Windows WaveOut handoffs took 78–94 ms apiece in a local test with a
48 kHz synthetic source; the worker stayed alive and reported zero underruns.
Actual audio, device drivers, decoder complexity, and visualizer load can vary.
Taps faster than a decoder can prepare remain queued in order, so an audible
snippet after *every* arbitrarily fast tap cannot be guaranteed. A real
listening test with the user's music and output device is still needed.

## V599 locked bass default and Emojimaxx wording

On a new installation with no saved `ReduceBassWhenLocked` value, **Reduce bass while computer is locked** starts on at 50%. The switch and percentage are in Web Config's Playback controls. Turning the switch off restores the normal unlocked bass setting without disabling PAFPlayer's Windows lock-screen song and lyric status. An existing saved on/off choice still wins over the new default. The session-only `--bass-reduction-while-locked` and `--no-bass-reduction-while-locked` options still take precedence for that run.

Emojimaxx now leaves the lyric word `heavy` as text instead of replacing it with a mechanical-arm emoji. Other Emojimaxx words and the directional arrow glyphs remain unchanged.

## V591 live bass transitions

The buffered WaveOut renderer now changes its running FFmpeg bass filter when
Windows locks or unlocks. It keeps the decoder, audio worker, queued PCM, output
device and playback clock running. Web Playback bass controls use the same live
path, including enabling or disabling bass boost. This removes the deliberate
stop/relaunch gap introduced by changing the filter in earlier versions.

The existing 120 Hz low shelf, percentage mapping, filter order before speaker
expansion, setting IDs and CLI overrides are preserved. Each selected output
receives the change. The named filter remains available at 0 dB so unlocking can
restore normal bass without rebuilding the stream. Commands use a private pipe,
not the user's console, and no extra DSP dependency is required.

Windows lock detection still runs once per second. Existing decoder/output
queues must drain before a change becomes audible; V591 does not promise an
instant change at the exact lock event. Legacy FFplay still needs the existing
same-position restart and can have a gap. Use the buffered renderer for this fix.
The running V590 process must be restarted to load V591.

Verification: 69 of 70 focused and relevant existing tests passed. The remaining
`test_seek_restarts_ffplay_at_requested_offsets` failure (expected three commands,
got two) is already recorded against V589 and V590; it is not introduced here.
An actual FFmpeg 4.2.3 stream at 96 kHz / 8 channels / 24-bit delivered all 672,000
frames while switching 0 → -14 → 0 dB. Every 10 ms block retained audio and the
final marker survived. A real Windows WaveOut worker, muted for testing, retained
one PID through both changes, reached six seconds and reported zero underruns.
No listening test of V591 has been performed yet.

Manual verification:

1. Restart the normal player with V591 and the buffered renderer enabled. Keep
   the existing bass-reduction checkbox and desired reduction amount selected.
2. Play a track with sustained bass, lock Windows for about 15 seconds, then
   unlock. Bass should reduce and restore without an intervening silence or a
   song-position jump. Allow the one-second polling and existing queued audio.
3. Adjust the bass controls in Web Playback while playing; confirm the same
   uninterrupted behavior. If using several output devices, check each one.
4. Repeat across pause/resume and a natural song ending. Paused/queued audio can
   delay the audible filter update; the ending should still play completely.

FFmpeg documents runtime bass-gain commands in its
[bass filter documentation](https://ffmpeg.org/ffmpeg-filters.html#bass_002c-lowshelf).
The private Windows stdin command path was also verified against the installed
binary, with successful command replies and measured decoded audio.

## V578 shuffle-aware transition preparation

The background successor worker predicts the normal forward track after queue
rotation and recent-play cooldown. Manual next-track requests, a pending resume
successor, and forward navigation history take priority in the same order as
the live playlist controller. File and history checks run after the current
decoder has had a three-second head start, outside the playback owner thread.
Random selection or a queue edit made after the prediction may still choose a
different song. Each track still starts a new decoder/output process; V578
therefore reduces avoidable preparation but does not promise gapless sound.

## V577 transition preparation and HUD corrections

For playlist playback, a background worker now warms the likely successor's
shared duration/tag probe, ReplayGain decision, edge-silence bounds, and console
cover rendering while the current song plays. The worker starts after a short
delay to let the current decoder begin first, and only one such worker runs at a
time. Its results feed the existing caches at the next track handoff. Manual
queue edits, shuffle changes, or very short songs can select a different track;
those cases still perform normal preparation. This reduces avoidable startup
work but does not yet guarantee gapless audio, because each track still creates
its own decoder/output stream.

The metadata HUD aligns an album value with the same album name in the visible
Play path when a one-cell adjustment fits within the existing whitespace. This
corrects the reported Vial / Grow Up path without shifting other field stops or
truncating data. Emojimaxx leaves `graveyard`, `graveyards`, and `fried` as words.

## V522 household control keys

The web **Control** section enables or disables this player's global Windows control hotkeys. The setting defaults on and is saved as `ControlHotkeysEnabled`. Ctrl+Alt+Up/Down repeats for volume, Ctrl+Alt+A raises album art, Ctrl+Alt+F toggles floating lyrics, and Win+C pauses/resumes. A separate `--tray-only host:port` client may relay these actions to the verified official owner; its Ctrl+Shift+Alt+A/F chords toggle the artwork and lyrics windows on that client computer. The remote switches are per-machine settings. See [Windows tray](windows-tray.md) for menu and timing details.

## V521 responsive Windows audio controls

With the buffered WaveOut backend, volume controls and web volume settings change the gain of the running PCM stream. They no longer stop and relaunch FFmpeg. The global Ctrl+Alt+Up/Down shortcuts repeat after a short hold delay and then about every 85 ms while held; ordinary console Up/Down also follows Windows key repeat. The audible gain change follows the queued audio reservoir, normally within the configured buffer duration (250 ms by default).

Pause and resume retain the same decoder and WaveOut output, so toggling either way does not incur a fresh decoder launch. A seek starts a replacement buffered stream at the target while the old stream continues, then switches outputs when the replacement has its short 50 ms preroll. This prevents the former stop-first silence, although a seek can still take time to decode and the console action loop waits for that handoff. The fallback FFplay backend still restarts for volume, pause, and seek, and format, speed, and effect changes may still require reconstruction.

The visualizer now labels a transition from playing to paused **Pause**, and a transition from paused to playing **Unpause**.

## V492 track handoff

## V495 fast Ctrl+Break

Ctrl+Break (and Ctrl+C) restores the terminal and stops the audio child immediately. A 1.5-second watchdog now ends the process if a non-daemon artwork GUI thread or another cleanup step cannot finish. Interrupts during the gap between tracks also use this fast path. The watchdog is a last resort and can skip normal final persistence; routine exits still perform their usual cleanup.

Web queue status can now be requested during startup, before the first audio path is selected, without raising an uninitialized-current-track error.

## V494 track transition lock reduction

The V493 trace showed unchanged settings taking effectively 0 ms, while shuffle rotation waited 2.27 seconds and selecting the successor took another 1.98 seconds. Web queue snapshots previously held the playlist lock while scanning missing files and checking every queue path. V494 copies queue state under the lock and performs those file checks afterward. The background shuffle rebuild also writes its cache from a copied snapshot after releasing the lock. The running V493 process is unchanged; transition timing for V494 requires a user-run instance.

Track transitions save only player settings changed since the session loaded or the previous handoff. Live control changes still persist; an unchanged track no longer rewrites every registry setting before the next song. The currently running V491 process needs a restart to use this change.

# Playback control notes

## V614 inline F2 rename

Press `F2` to edit the current filename directly in the controls row. The
existing filename is filled in, with the visible caret just before its audio
extension. Type normally, use Left/Right, Home/End, Backspace or Delete, then
press Enter to rename or Esc to cancel. The filename stays unchanged until
Enter. The prompt remains open if the song finishes or the player advances to
another track; the rename still targets the song selected when F2 was pressed.
Music and the visualizer continue during editing. Global media controls and
remote/web transport remain active. Long filenames scroll within the prompt so
the caret stays visible.

The V587 hard-link staging still handles a rename committed while that song is
playing. If the song has finished and a different track is playing, PAFPlayer
renames the original file normally and repairs the configured playlist/queue
references. The old name of a staged live rename retires after its decoder
closes.

## V587 live F2 rename

Press `F2` during playback or while paused to edit a filename. The audio
decoder keeps playing while the editor is open. On Windows, FFmpeg holds its
source file open in a way that prevents an immediate ordinary rename. PAFPlayer
therefore creates a second hard-link name for the same file, updates its active
playlist and queue references, and keeps playback on the original open handle.
After the track's decoder closes, PAFPlayer sends the old filename to the
Recycle Bin. No audio decoder or output device is restarted for the rename.

The new and old names refer to the same bytes until cleanup. This requires a
hard-link-capable volume and both names in the same directory. If the volume
does not support links, the rename reports an error and the song keeps playing.
If another program keeps the old name open after PAFPlayer stops, recycling may
fail; PAFPlayer reports the remaining name and leaves it in place. `Ctrl+F2`
selects the previous karaoke style; `F3` selects the next.

## V576 command-line seek handoff

While the official PAFPlayer instance is running, launch a second normal command
with a standalone timestamp: `PAFPlayer 0:30`, `PAFPlayer 1:30`, or
`PAFPlayer 125s`. It forwards a seek to the playing official instance, including
while paused; it does not start another player. Negative forms count backward
from the track end: `PAFPlayer -5s` and `PAFPlayer -1:30`. Positions outside
the playable track clamp to its beginning or end. A negative seek requires a
known duration. With no official instance running, a timestamp alone reports an
error rather than opening a file named like a time. This handoff uses the
existing authenticated single-instance channel; `--instance` cannot target
another player with a standalone timestamp.

## V575 readable rainbow volume

The compact console volume readout retains its rainbow hue, but deep blue and
violet values are mixed toward white until they meet the same minimum
luminance used for the progress percentage. This keeps the icon and percentage
legible against the dark console HUD at every volume level.

## Console volume entry

PAFPlayer V489 opens the direct volume prompt with either lowercase `v` or capital `V` during active or paused playback, then accepts one of these commands:

- Type a percentage from `0` through `400` and press Enter, such as `50`, `100`, or `150`.
- Press Up or Down to apply a 20-point change immediately.
- Press `=` to restore 100% immediately.
- Press `P` to restore the volume that was active immediately before the last real volume adjustment. Repeating `V`, `P` toggles between the two most recent values.
- Press Esc to cancel without changing the volume.

The quick visualizer-mode keys are now `M` for next and `Shift+M` for previous. The existing function-key controls remain available.

## Bass Reduction while Locked

The Playback section of the web configuration contains a `Bass Reduction while Locked` checkbox and a dependent `Bass reduction amount while locked` slider. The slider is disabled until the checkbox is enabled and ranges from 0–100%.

The setting is applied through the decoder's bass filter while Windows is locked. PAFPlayer checks the lock state once per second and rebuilds the current segment only when the effective bass gain changes. Enabling the checkbox or editing its amount while unlocked saves the preference without interrupting playback. Changing the boost amount while boost is disabled also avoids a restart. Audible changes use the short interactive preroll; unlocking restores the normal bass settings when needed.

V485 reads only the four bass settings for this check and prevents a direct control change from triggering a second restart through the lock monitor. See [performance details and validation limits](performance-v485.md).

V489 republishes all four bass values immediately after a web change and synchronizes the dependent slider after restoring checkbox state. Consequently, `Bass Reduction while Locked` remains checked after web polling, configuration reload, and restart; its durable value continues to be stored as `ReduceBassWhenLocked`.

### V590 lock-detection and restart repair

V590 queries the calling Windows session's explicit lock/unlock flag using
[WTSQuerySessionInformationW](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/nf-wtsapi32-wtsquerysessioninformationw).
It no longer tries to switch desktops as a lock test. During a real Windows 10
lock/unlock trace on this computer, the session flag correctly stayed locked
while the input desktop was sometimes accessible. At other times the old
checker saw ctypes error 0 even though Windows returned access denied (5).
Private, fully typed API wrappers now capture errors correctly; a read-only
input-desktop query remains a fallback if session information is unavailable.
No UAC or Windows configuration change is required.

The bass-change restart now exits the playback polling loop explicitly and
rebuilds the same track at its current position. The former `continue` could
enter the loop's natural-end branch after stopping the decoder and advance to
the next song. Changes still use the existing short interactive preroll, so a
brief decoder restart can be audible; this release does not claim seamless EQ.

The percentage is the existing shelf-control scale, not a linear percentage of
overall volume: 70% reduction without boost requests a -14 dB low shelf at
120 Hz. An actual decoded-audio test measured approximately -14.7 dB at 40 Hz
and +0.1 dB at 1 kHz; unlocking restored identical decoded samples. Boost and
lock reduction still combine through the same bounded ±20 dB shelf.

For diagnostics, `/api/status` includes `session_locked` and
`bass_effective_db`, refreshed by the existing one-second playback check when
state changes. They start as null until the first check and represent the last
playback observation, not continuous monitoring while playback is stopped.

Manual check: restart with V590, enable the existing checkbox and select a
nonzero amount, then play a bass-heavy track. Lock Windows for at least five
seconds, confirm the bass drops without changing songs, then unlock and confirm
normal bass returns. The live lock detector and decoded filter were verified
separately; listening to the household player's output after upgrading remains
this final manual check. Saved setting IDs, preferences, and CLI overrides are
unchanged.

## Floating Lyrics title period

`Display song title for first` is a floating-point number of seconds (0–60, with 0.01-second web precision). The default is 25 seconds when no saved value exists. The canonical persisted setting is `FloatingLyricsTrackIntroSeconds`; older installations using `FloatingLyricsTrackIntroMs` are read as a migration fallback. Web-console changes are saved as seconds and immediately published to the running player. On startup, PAFPlayer applies the saved value to the live Floating Lyrics timer, and track transitions retain the current value without resetting it.
# V542 Test Tone studio

The Speaker Expansion Matrix now contains a persistent-session **Test Tone**
studio. `Ctrl+T` toggles it during playback. It uses PAFPlayer's selected output
device, sample rate, bit depth, and stereo/5.1/7.1/Atmos native WaveOut layout;
the tone generator does not replace or reconfigure the music stream.

Each tone independently stores frequency (20–20,000 Hz), one of five patterns
(continuous, one-second pulse, warble, slow sweep, or burst), and volume
(0–50%). Any number of simultaneous tones can be added. The web editor exposes
exact number/range/select controls and remove buttons.

While Test Tone mode is enabled:

- held Left/Right arrows or left/right mouse buttons lower/raise the selected
  tone by semitones;
- held Up/Down arrows select the next/previous pattern;
- middle mouse or `Shift+T` selects the next tone;
- triple left/right click, `Alt+T`, or `Ctrl+Alt+T` adds another tone;
- `Ctrl+S` prompts for a description and saves the complete set;
- `Ctrl+L` lists saved sets one per line with date, description, frequencies,
  tone numbers, and a compact waveform representation, then loads a selection.

Named sets are stored in PAFPlayer's main per-user configuration registry value
`TestToneSetsV542`. The same save/load controls are available in Web Config.

# V550 floating-lyrics glyph-only clicking

In normal display mode, the floating-lyrics window captures a mouse click only
when the pointer is over a genuinely painted lyric glyph pixel. Transparent
padding, spaces between letters, line gaps, and the rest of the window pass the
click through to the application underneath. Colored emoji glyphs participate
in the same pixel-level hit mask. Holding `Ctrl` still makes the whole overlay
interactive for moving/resizing, and explicit edit mode remains fully
interactive.

# V549 persistent bass CLI settings and defaults

The spelling of a bass CLI switch communicates whether it is temporary or
durable:

- Bare `--bass-reduction-while-locked` and
  `--no-bass-reduction-while-locked` remain session-only.
- `--bass-reduction-while-locked=on|off` updates the saved Web Config checkbox
  and also applies the choice to the current run.
- `--locked-bass-reduction-percent=N` remains session-only.
- `--default-bass-reduction-percent-while-locked=N` saves the user default used
  by PAFPlayer's restore-default controls. Valid values are 0–100; **50% is the
  factory-reset default**.

# V548 working locked-bass reduction and CLI overrides

The default buffered WaveOut renderer now inserts the same low-shelf bass
filter that the legacy FFplay path already used. PAFPlayer continues checking
the Windows lock state once per second; crossing the lock boundary rebuilds the
decoder at the current position only when the effective bass gain changes.

These bare/session-value command-line overrides do not alter Web Config or
registry preferences:

- `--bass-reduction-while-locked`
- `--no-bass-reduction-while-locked`
- `--bass-reduction-while-locked=on|off`
- `--locked-bass-reduction-percent=0..100`

Example: `PAFPlayer.py --bass-reduction-while-locked --locked-bass-reduction-percent=60 song.flac`.

# V547 explicit repeat and Test Tone HUD

The console controls row spells out **Repeat track** whenever single-track
repeat is active instead of showing an ambiguous loop glyph alone.

While Test Tone mode is active, that HUD row is replaced with the selected
tone number, frequency, pattern, and volume followed by the live controls:
Left/Right for pitch, Up/Down for pattern, middle-click or `Shift+T` for the
next tone, `Alt+T` to add, `Ctrl+S` to save, and `Ctrl+L` to load.

# V546 Emojimaxx clarity

Emojimaxx no longer replaces the ordinary words `entire` or `powder`; those
substitutions were too surprising in normal lyrics. The singular word `secret`
now uses 🤫 (shushing face), which communicates “keep this quiet” more directly
than the previous locked-padlock symbol. The plural mapping remains separate.

# V545 ordered-help sorting and reliable tray refresh

The alternate key-ordered `?` help view always lists ordinary `A` through `Z`
keys first, followed by `F1` through `F10`, then punctuation, navigation, and
other keys. Modifier variants remain together on the base key's one line.

# V544 ordered help, Discord profile activity, and tray gallery

- In the `?`/F1 console help overlay, pressing bare Shift, Ctrl, or Alt switches between the section-organized view and a one-binding-per-line key-order view. The latter sorts A–Z, then F1–F10, then other keys and gives each row a distinct color.
- `Shift+F2` is the preferred karaoke-treatment-previous shortcut; `Ctrl+Shift+F2` remains an equivalent alias.
- Discord integration now updates the user's profile through local Discord Rich Presence, not a channel webhook.
- The progress demo label explicitly names Style 1, Spectral Flux, Beat illumination, and Flash Full.

# V543 rename-current-file and web configuration cleanup

- `F2` renames the currently playing audio file without changing its audio extension. Playback resumes from the same position using the new path.
- The Playlist tab contains **Repair current playlist when we rename a song with the F2 key** and its dependent **Search for other playlists to repair as well** option. Enabling current-playlist repair enables the broader search by default; it can then be turned off independently. Playlist replacements receive verified sibling backups before they are written.
- The former `F2` karaoke-previous command is now `Ctrl+F2`; its former `Shift+F2` treatment command is now `Ctrl+Shift+F2`. `F6` and `Shift+M` remain the visualizer-navigation shortcuts, so the old duplicate `Ctrl+F2` visualizer alias was removed. Megamix now uses `Ctrl+F2+F3`.
- The web tabs now begin Playback, Tags, Metadata / Maintenance. Repair controls live under Playlist, and Artwork Actions live under Artwork.
- Tags uses **Show tags** / **Hide tags**. The beat timing control has no experimental badge, its `ms` suffix no longer overlaps the input, and the progress-bar demo names the settings it temporarily demonstrates.
- Live logs render newest first. Global Hotkeys reports current player state and asks for confirmation before disabling. Tray-hover failures are logged without spilling callback tracebacks into the console.

## V582 Emojimaxx cleanup

Removed the low-value Emojimaxx substitutions for `broth`, `grown`, `lean`, and
`kidding`. The words now remain ordinary text when Emojimaxx is enabled.

