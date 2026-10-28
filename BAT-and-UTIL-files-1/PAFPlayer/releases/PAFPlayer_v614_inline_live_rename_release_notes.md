# PAFPlayer V614 — inline live rename

F2 opens a prefilled filename editor in the console controls row. The caret is
visible, starts before the extension, and stays visible as the user edits a
long filename. Left/Right, Home/End, Backspace and Delete work within the name;
Enter commits and Esc cancels. The file and active queue are unchanged until
the commit.

The editor is nonblocking. Playback, visualizer rendering, media keys and web
controls continue, and a song can finish and advance to the next track before
the edit is submitted. The pending edit still targets the original song. A
rename committed during that song's playback uses the existing hard-link staging
and retires the old name after the decoder closes. A rename committed after the
track ends uses an ordinary rename and updates the configured playlist and
in-memory queue references.

Verification: focused V614, V587 and V543 tests; playback/delete regression
tests; Python compilation; single-file layout checks. An actual interactive
Windows Terminal session was not available for visual caret inspection, so
terminal-specific rendering remains a manual check.
