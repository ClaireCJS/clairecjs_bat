# PAFPlayer V669 — Visible extended-command prompt

Typing `#` displays the command and an insertion marker in the console while music plays or is paused. Backspace edits; Escape cancels. Enter or 1.5 seconds of inactivity submits a nonempty command, and an empty prompt disappears. The current display is restored on dismissal; Help and tag views retain prompt visibility.

Verification: 16 focused tests passed, including mocked playing, paused, and Help prompt rendering, command editing, timeout, and cancellation. All 28 bundled modules compiled and matched editable sources; the release matches the active player. [Test report](../tests/reports/v669-hash-prompt-checks-20261112.json).
