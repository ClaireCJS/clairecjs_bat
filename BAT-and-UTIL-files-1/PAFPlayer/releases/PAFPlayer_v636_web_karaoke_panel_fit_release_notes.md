# PAFPlayer V636 — Web Karaoke panel fit

November 1, 2026

- **Auto-Expand Lyric Size** now chooses the largest font that fits the current
  lyric within the assigned web lyric panel, growing short cues and shrinking
  long ones when the ordinary size would clip.
- Corrected the horizontal overflow test: `scrollWidth` already includes the
  full element width, so adding a safety margin had caused every normal lyric
  to fail the fit test and remain at its base font size.
- Long unbroken words can wrap within the panel. A small edge margin remains.
- The checkbox and panel-height preference keep their existing storage and
  behavior. Console karaoke and native floating lyrics are unchanged.

Focused tests include a real headless Microsoft Edge layout check at small and
large panel heights with short, long, and unbroken lyrics. The test verifies
that the chosen text fits and that increasing its size by 5% would not fit.
Python syntax, relevant existing tests, and release source parity were checked
separately.
