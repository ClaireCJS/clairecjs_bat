# PAFPlayer V529 release notes

Released October 12, 2026.

- The embedded Windows lock-screen companion is now version `529.0.0.0` with a
  V529 first-run marker and cache path. A normal first run detects V528 and
  upgrades it; an already installed V529 is left untouched.
- Routine upgrades use the already trusted PAFPlayer certificate and do not
  require renewed elevation. Missing or changed certificate trust still invokes
  Windows UAC.
- Emojimaxx solution labels receive a small rightward optical correction equal
  to 2% of the primary lyric font size in Web Karaoke, Floating Lyrics, and
  Artwork Lyrics.
- The signed MSIX, pinned certificate, installer, and integration remain embedded
  in the single-file player and available through `--install-lockscreen` and
  `--check-lockscreen`.
