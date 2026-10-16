# PAFPlayer V481 release notes

## Playback configuration

- Added a functioning `Bass Reduction while Locked` checkbox with a dependent 0–100% reduction slider.
- Bass filter changes and Windows lock/unlock transitions now rebuild the current playback segment so the configured state is actually applied while the song continues.
- Floating Lyrics `Display song title for first` is now stored canonically as a floating-point number of seconds. Existing millisecond settings remain readable as a compatibility fallback, while web-console edits save the new seconds value correctly.

## Compatibility

- Existing configuration keys for the bass controls remain unchanged.
- The legacy `FloatingLyricsTrackIntroMs` value is not used as the canonical write target anymore.
