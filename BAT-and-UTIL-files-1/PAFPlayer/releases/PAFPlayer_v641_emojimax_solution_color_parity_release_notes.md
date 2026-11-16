# PAFPlayer V641 — Emojimaxx solution color consistency

November 2, 2026

- Web Karaoke's hover answer now uses the configured solution color when
  inheritance is off and the current lyric color when inheritance is on.
- Floating Lyrics samples a solid source glyph pixel for inherited answers,
  excluding the black shadow or outline. It refreshes inherited answer colors
  during lyric color animation, with a 160 ms minimum between small-label
  repaints to avoid adding work to every frame.
- Native hover answers use the same color as their visible small answer.
  Fixed-color answers do not change with lyric animation.
- Web Karaoke, Floating Lyrics, and Artwork Lyrics continue to keep separate
  saved appearance settings. Matching treatment requires choosing the same
  fixed/inherited option in each relevant section; their underlying lyric
  coloring modes can still differ.
- Focused tests cover fixed color, inherited color, shadow rejection, web
  color choice, and fallback when no source glyph is available.
