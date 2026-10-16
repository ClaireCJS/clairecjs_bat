# PAFPlayer V114 release notes

Release: **V114**  
Build: `2026-08-10-shared-replaygain-reliability-art-and-web-v114`

V114 is a cumulative application-and-documentation release centered on one shared ReplayGain implementation, observable history/Last.fm reliability, safer HUD geometry, cleaner artwork/lyric windows, completed playlist-selection workflows, and a MiniLyrics-inspired local web presentation.

## Shared ReplayGain baking

- `ClaireAudioProcessing.py` now owns the complete destructive bake transaction for both PAFPlayer and `audit_music_batch.py`; there are not two copies of the algorithm.
- `Ctrl+Alt+B` confirms, stops FFplay, bakes the current FLAC/MP3 adjustment, refreshes tags, and resumes at the same playback position.
- The shared routine peak-limits positive gain, stages and validates the new media, makes a verified timestamped backup, replaces atomically or with SHA-verified fallback, regenerates/validates ReplayGain tags, and rolls back on failure.

## Playback reliability and HUD

- A Last-play write is successful only after SQLite commit and exact-row read-back. Failure is logged and shown as a blinking warning; learned marking reports partial success separately.
- Last.fm Now Playing is again dispatched independently of scrobbling, immediately after a successful FFplay launch and within the traced five-second boundary.
- Frequency Warp is normal default-on behavior, not experimental. `FrqWrp` appears only for a nondefault setting and never obscures a changing volume marker.
- `✅Learned` appears when the effective attributes include `learned`.
- Colon alignment can no longer create an avoidable metadata row. If metadata truly needs more height, the visualizer yields a row so the grey status bar retains its own row. Directory visibility is recomputed after history completion and resize.

## Artwork and lyrics

- Previous/current/next lyric ordering is consistent end-to-end, removing the one-cue delay in floating and over-art lyrics.
- Native lyric rainbows now take 14 seconds per cycle and glyphs use an approximately one-point eight-direction outline.
- Artwork border and the larger centered control strip are focus-only. The `◐` button reveals a persisted over-art opacity slider.
- Letterbox space is transparent, and unfocused native hit testing passes clicks through pixels outside the actual art.
- The title/identity fit is recalculated from the current resized window. A fitting identity uses the full width without marquee and is centered.
- Clicking floating lyrics makes the decorated interaction window opaque; it returns to transparent click-through presentation after interaction.
- Manual idle invocation now animates the primary art window as well as safe related-art windows.

## Playlist, Help and catalog

- J/Q now has visible Queue selected, Jump to one, and Cancel buttons in addition to Enter/Shift+Enter/Esc.
- `--catalog-file PATH` chooses an INS catalog. If the requested file is absent, the daemon catalog worker builds it atomically from the configured music root.
- Help places its divider after ReplayGain/playlist diagnostics, documents INS/J/Q, and uses D to toggle the current-directory line while the overlay is open.

## Web controller

- A MiniLyrics-inspired left pane splits vertical space 50/50 between album art and large synchronized karaoke, with a browser-local Emojimaxx checkbox.
- With no lyrics, the karaoke pane withdraws and all related artwork becomes available in a full-height scrollable gallery.
- Artist and Song share `Artist — Song`; clicking the full path opens its folder in Explorer.
- Time/progress, five transport buttons, volume, speed and balance share one compact row. `⏯` genuinely toggles pause and resume.
- Tags appear above Choices. Playlist / Metadata is the first Other actions group.
- Dropdowns mark saved favorites with `⭐` and effective defaults with `✨`.
- The related-art tooltip exists only when previous/next images exist.
- Web karaoke rainbow is 25% faster. The visualizer samples the selected terminal palette and reverse direction while preserving the small 20-Hz analyzer stream and display-rate canvas interpolation.

## Verification and files

- The embedded player suite passes **372 tests** with **3 expected optional/platform skips**.
- `ClaireAudioProcessing.py`, `audit_music_batch.py`, and both canonical/descriptive PAFPlayer sources compile successfully.
- The release includes the source files, complete current manual, cumulative changelog, these notes, 20 status-line mockups, checksums, and a ZIP with the same verified contents.

See `play_audio_file.md` for the current manual, `PAFPlayer_changelog.md` for cumulative rationale, and `PAFPlayer_v114_status_line_mockups.md` for the requested discussion artifact.
