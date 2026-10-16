# PAFPlayer V430 — safe Windows console Unicode writes and Emojimaxx cleanup

September 22, 2026. Build `2026-09-22-v430-console-unicode-chunking-and-emojimax-cleanup`.

V430 completes the active PAFPlayer TODO list. The final Emojimaxx curation
layer removes the requested `true`, `false`, `aren't`, `swear`, `good`, `bad`,
`starting`, `ending`, and `welcome` substitutions. `ladies` now uses a
distinct feminine pair glyph (`👩‍🤝‍👩`) instead of reusing the `men` mapping.

Large writes to a real Python `_WindowsConsoleIO` TTY are now limited to 4,096
characters and flushed after each chunk. The logical payload remains under the
existing console lock, so ANSI order, cursor markers, and frame accounting are
unchanged. Short writes and redirected output keep the single-write path.
Explicit binary terminal payloads remain bytes throughout, and both binary
stream writes and optional direct file-descriptor writes now complete partial
writes without decoding, dropping, or replaying an already-written prefix.
Some Windows console adapters return `None` after accepting a complete text
write; V430 now treats that result as complete instead of aborting playback or
duplicating the chunk.

Validation: 8 new V430 transport/curation tests, the 18 focused V416/V429
regressions, and source compilation passed. The tests cover the reported
15,000-character half-block shape, a multi-byte glyph at a chunk boundary,
surrogate-pair boundaries, redirected output, text partial writes, and binary
partial writes. A real hidden-console private-buffer comparison was not
available in this session, so Windows Terminal rasterization remains a manual
follow-up; no playback or user settings were changed during validation.

Restart PAFPlayer to load V430.
