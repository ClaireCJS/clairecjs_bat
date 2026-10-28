# PAFPlayer V573 — lyric character recovery

Floating Lyrics now displays the character reported as `` (U+0089) as `‰`, its printable Windows-1252 equivalent. Other defined Windows-1252 punctuation in the U+0080–U+009F range is recovered the same way. Recovery occurs when lyric text is read and again before a floating cue is drawn, so a direct runtime update is covered too.

Sidecars with invalid UTF-8 now fall back to Windows-1252 decoding. Sidecar and audio files are not rewritten. Existing UTF-8 and UTF-16 lyric reading remains in place.

Verification: all four focused regression tests and Python compilation passed. A Pillow floating-lyric mask rendered `5‰ chance` successfully. The existing floating-cue timer test passed; its companion historical mask-comparison test could not run because the referenced V485 source file is absent from this checkout. A real floating-window check on the user's track remains to be done.
