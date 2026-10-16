# PAFPlayer V501 — Floating Lyrics title duration persistence

Fixed fractional values for **Display song title for first X seconds**.

The live web update already accepted fractional seconds, but later normal
settings flushes and Global Config profile restores converted the value to an
integer DWORD. Values such as `0.25` could therefore become `0` or otherwise
lose their fractional portion.

V501 stores `FloatingLyricsTrackIntroSeconds` as a string-formatted floating
point registry value in every persistence path, while retaining the existing
DWORD behavior for integer settings.

Validation: Python compilation and three focused persistence regression tests
passed.
