# PAFPlayer V600 release notes

## Delete, save, and undo

Delete removes the current track from the active playlist, manual next queue,
and visit history immediately. It does not delete the audio file or interrupt
the current playback stream. The subsequent **Save deletion to {playlist
filename}?** prompt defaults to Yes after eight seconds. Enter/Y saves the
edit; N keeps it only for the current session; Esc/Ctrl+Z cancels and restores
membership. The confirmed web removal and learned-song R removal still save
directly.

Ctrl+Z after the prompt restores the latest playlist deletion, including the
playlist file if it was saved. A setting change gets the next undo first. A
newer playlist edit supersedes the one-step deletion undo. Undo refuses to
overwrite a playlist changed on disk since the deletion. Playlist-file writes
create verified sibling replacement backups.

The active queue and visit history exclude a removed track, so Next followed
by Previous cannot return to it. If no playlist members remain, the next
transition ends playback instead of reopening the removed song.

## Verification and limits

Twenty focused and related pytest cases and seven embedded playlist tests
passed. The tests cover the eight-second default, explicit choices, disk
backup/restore, changed-file refusal, continued playback, Ctrl+Z routing,
and navigation over a pruned history. Python compilation checks passed.
No live Windows console/audio listening test was performed for V600. One
existing learned-song test emitted a subprocess ResourceWarning after passing.
