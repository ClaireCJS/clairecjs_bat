# PAFPlayer V494 — October 4, 2026

- Floating, Web, and Artwork Lyrics each have separate Emojimaxx solution visibility, size, distance, over/under, color, opacity, and inherit lyric colors controls. Defaults: 20% size, 1 px under, 100% opacity.
- Floating and artwork solution labels render with alpha, and inherited colors follow the rendered lyric colors.
- Mixed emoji runs use a symbol fallback per supported cluster when the preferred emoji font lacks a glyph.
- Web queue file scans and background shuffle cache writes no longer hold the playback queue lock. This targets the multi-second waits observed in V493 transition traces. Live V494 timing remains to be checked when the user runs it.
