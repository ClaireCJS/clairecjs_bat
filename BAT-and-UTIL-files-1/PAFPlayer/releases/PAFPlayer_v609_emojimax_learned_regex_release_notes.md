# PAFPlayer V609 — Emojimaxx and learned regexes

- Emojimaxx no longer substitutes `product` with `∏`. Existing Whip mapping
  remains `𓀓𓀝`.
- New numbered-track selectors saved to `attrib.lst` use separator-aware
  prefixes such as `^05[ _-]` and `^4[ _-]01[ _-]`. They no longer end in `.*`.
  The existing sibling-collision check remains in place, and the writer rejects
  any selector that still ends in `.*` before creating or changing the file.
- Existing `attrib.lst` records, configuration, playback, and media files are
  not migrated or rewritten by this release.

Focused tests cover literal `product`, preserved Whip substitution, numbered
track selectors, saved-rule specificity, and the writer guard. The Whip glyphs
have not yet been visually verified on the physical remote tray computer.
