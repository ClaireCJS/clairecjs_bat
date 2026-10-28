# PAFPlayer V587 — live F2 rename

Released October 20, 2026.

Pressing F2 while a song is playing now opens the filename prompt without
stopping or pausing the decoder. A blank answer cancels without a playback
restart. A valid answer stages the new name as a hard link to the same audio
bytes, updates the in-memory playlist and queue paths, and applies the existing
optional playlist-reference repair settings. After playback releases the
source, PAFPlayer sends the old name to the Windows Recycle Bin. The new name
is available immediately and the same audio stream continues throughout.

This method is necessary because Windows blocks ordinary renames while FFmpeg
holds the file open. During the remainder of the track, both filenames refer
to the same file. A hard-link-capable filesystem and same-directory rename are
required. If linking or final recycling fails, PAFPlayer leaves the original
untouched and reports the problem. An abnormal process termination can leave
both names; the old name is not permanently deleted. The decoder is not closed
and reopened at the F2 prompt, because doing so would risk a gap. This release
does not claim sample-perfect hardware gaplessness across external device or
decoder failures.

The main manual now correctly lists F2 for rename, Ctrl+F2 for the previous
karaoke style, and F3 for the next style. V586's install survey remains present.

Validation: the focused V587 tests cover live file identity, Windows FFmpeg
continuing to read through the rename, playlist repair, chained renames,
collision refusal, and guarded Recycle Bin cleanup. The V586 survey tests,
existing F2 key-mapping test, and Python syntax check also pass.
