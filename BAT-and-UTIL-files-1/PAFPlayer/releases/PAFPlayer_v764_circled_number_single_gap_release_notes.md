# PAFPlayer V764 — one visible circled-number gap

Restore exactly one Windows Terminal compatibility cell after each contiguous run of bold circled-number substitutions. Double-height rendering consumes that cell; the lyric's normal separator remains as the single visible gap before the next word. Contiguous number glyphs stay together and receive padding only after the run. The separate pen glyph workaround is unchanged.

## Validation

The embedded checks cover a single ❶, adjacent circled glyphs, a ❹⓿ compound, lyrics with one source separator, and all ❶–❿ markers. The active runnable source was syntax-compiled and copied byte-for-byte to the release artifact. Use `pafplayer --emojimax "4 3 2 1 5 6"` to inspect number glyph rendering in the console.
