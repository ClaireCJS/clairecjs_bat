# PAFPlayer V496 — October 4, 2026

- Fix floating lyric lines blanking when an Emojimaxx solution image is drawn. The live V494 errors showed an undefined `window` reference in that path. Answer rendering failures now leave the main lyric visible.
- Add persistent Artwork and Floating Lyrics solution controls to Web Config, including size, distance, over/under, inherit lyric colors, color, and opacity.
- Give Web, Artwork, and Floating Lyrics Emojimaxx controls a separate row in each configuration section.
- No player process was launched or restarted while preparing this release.
