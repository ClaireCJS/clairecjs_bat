# PAFPlayer V640 — loopback reconnection and Unicode floating lyrics

November 2, 2026

- The RAM loopback input now enables FFmpeg's bounded HTTP reconnection. The
  local server supports Range requests so decoding can resume from the needed
  byte offset after an interrupted read. Direct-file inputs are unchanged.
- V639's early-end detection remains a fallback if reconnection cannot finish
  the track. An actual interruption may still cause a brief audio gap while
  reconnecting or switching to the source file.
- Floating Lyrics selects an installed font with Japanese glyphs when Segoe UI
  lacks them, including fonts packaged as TrueType collections. It preserves
  the current primary font for glyphs that font already supports.
- Focused tests cover command construction, Japanese glyph coverage, and TTC
  reading. The reported Red Hot Chili Peppers MP3 has an opt-in muted,
  isolated whole-track check; it skips with a warning if the source file or
  output device is unavailable. It does not contact the official player.

The exact cause of an interrupted Windows loopback read can depend on the
local FFmpeg build and Windows network stack. Font fallback depends on which
fonts are installed. Neither change edits audio files or saved settings.
