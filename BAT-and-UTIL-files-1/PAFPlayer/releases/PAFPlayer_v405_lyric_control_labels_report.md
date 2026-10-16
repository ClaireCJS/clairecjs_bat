# PAFPlayer V405 lyric control labels

Updated the Web Karaoke controls:

- `Lyrics` and `Karaoke` both use the pencil icon (`✏️`).
- `Auto-Expand` now reads `Auto-Expand Lyric Size`.

Validation:

- Generated Web Karaoke HTML contains both pencil-labeled buttons.
- The old musical-note Karaoke label is absent.
- The new Auto-Expand label is present.
- Embedded web karaoke regression tests passed.
- Python AST parsing passed.

