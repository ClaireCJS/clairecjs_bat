# PAFPlayer V424 — compact HUD diagnostics

September 21, 2026. Build `2026-09-21-v424-compact-hud-diagnostics`.

## HUD packing

The optional HUD details surface now packs its ReplayGain and Playlist
diagnostics onto one ANSI-safe row whenever both rendered values fit in the
available terminal width.  When they do not fit, they remain separate rows.
Effective attribute tags still occupy the following row.  An unused former row
is explicitly cleared, so stale text cannot remain on screen.

## Eracist classification diagnosis

The inspected track is:

`C:\mp3\Mike Patton\Mr. Bungle\2020 - Raging Wrath Of The Easter Bunny (demo) (re-recording of 1986 release)\07_Eracist.mp3`

Its path contains no `[chiptune]` or `[sound effect]` marker; its inherited
attributes are only `changer` and `long`; and its embedded Genre is `Metal`.
PAFPlayer's lyric-expectation suppression recognizes only literal path markers
such as `[chiptune]`, `[sound effect]`, `[sound clip]`, instrumental/no-vocals
markers, or `audiobook`.  Therefore this player does not derive a chiptune or
sound-effect classification for that file; that label must come from another
classifier or a stale display state.

## Saved artifacts

- Canonical player: `play_audio_file.py`
- Versioned snapshot: `play_audio_file_v424_compact_hud_diagnostics.py`
- This description: `play_audio_file_v424_release_notes.md`
