# V444 — V427 plus the console row-alignment fix only

Built from the user's restored V427 on September 23, 2026.

Large non-ASCII writes to Python's native Windows console stream now use
`WriteConsoleW` directly. This avoids the Python 3.10.9 UTF-8 conversion bug that
turns a half-block into replacement characters and shifts subsequent cells.
The original payload, VT commands, and console lock are preserved. Short text,
ASCII text, redirected output, and binary output keep their V427 paths.

This is an isolated change to `write_console()` with two supporting helpers
and new version identifiers. An AST comparison verifies the rest of the entire
program is identical to V427, including rendering, FPS control, compositing,
popup behavior, lyrics, audio, and Emojimaxx. It does not reinstate V428–V443.

All seven focused tests passed. A real hidden Windows console reproduced three
replacement characters with the V427 writer. The fixed writer preserved 30,000,
40,002, and 120,000-character payloads exactly, with zero replacements and correct
subsequent cursor placement. A large ANSI-colored half-block payload preserved
every tested row. Other checks cover unchanged paths, exact VT payloads, locking,
cursor markers, UTF-16 surrogate units, and partial writes without prefix replay.

Run `python -B -X utf8 test_play_audio_file_v444_console_rows.py` to verify.
The user's console and playback were not used for testing.
