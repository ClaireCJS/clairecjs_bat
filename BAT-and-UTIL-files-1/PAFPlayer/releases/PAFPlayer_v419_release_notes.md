# PAFPlayer V419 — album-art emoji spacing

September 21, 2026. Build `2026-09-21-v419-album-art-emoji-spacing`.

## Fix

The album-art popup can replace lyric words with colored emoji.  On some Windows
color-font/Pillow combinations, the emoji font reported transparent right-side
cell padding as part of its advance.  The following source word separator was
then added after that padding, making the gap after an emoji-replaced word look
like two spaces.

The popup renderer now advances each colored-emoji run to the rightmost painted
pixel reported by its grayscale glyph mask, then preserves the single source
space.  Older or non-FreeType fonts fall back to the existing `textbbox` path.

The floating-lyrics renderer was deliberately not changed.

## Saved artifacts

- Canonical player: `play_audio_file.py`
- Versioned snapshot: `play_audio_file_v419_album_art_emoji_spacing.py`
- This description: `play_audio_file_v419_release_notes.md`

## Validation

- `python -m py_compile play_audio_file.py` completed successfully.
- The full historical `--unit-tests` run was started, but it remains not fully
  green because it reports unrelated legacy failures/errors, including
  `WinError 5` in playlist tests.

Restart PAFPlayer to load V419 if it is already running.
