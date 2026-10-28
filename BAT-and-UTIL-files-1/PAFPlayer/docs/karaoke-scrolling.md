# Console Karaoke scrolling

Sequential lyric lines use a two-step vertical transition. The intermediate
step places the line halfway through its upward scroll before the settled frame
is painted. Its duration is matched to the normal 5-Hz console karaoke refresh
cadence so the intermediate frame is not skipped.

When a new cue starts after the visualizer has expanded into otherwise empty
karaoke rows, the normal compositing mode paints the lyric first and then
resizes the spectrum. The three double-height lyric bands and any vacated rows
are submitted as one terminal update. This keeps the lyric transition from
waiting behind the first compact spectrum frame and prevents rows from
appearing one at a time. Visualizer-through-karaoke modes retain visualizer-first
painting so their masking and background sampling still work.

Emojimaxx renders `hot` as the emoji-presentation hot-springs symbol (`♨️`).
This makes its two-cell terminal width explicit, so the lyric's original space
before punctuation remains visible (for example, `Too ♨️ & too fast`).
Per-character rainbow and hashed colors treat an emoji with its presentation
selector as one display cluster, keeping the selector next to its glyph.
