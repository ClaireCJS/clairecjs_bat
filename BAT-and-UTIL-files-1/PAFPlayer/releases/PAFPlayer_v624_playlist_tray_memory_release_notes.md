# PAFPlayer V624 — playlist, tray, and memory playback

Released October 27, 2026.

- `--simple FILE` runs an independent, simple player. It neither forwards to the official instance nor claims its tray icon.
- Delete removes an active queued-only track even when the original playlist file has no matching row. The song continues playing; subsequent playlist navigation excludes it. Undo restores its live membership.
- The PgUp/PgDn playlist browser refreshes its visible page after an external queue insert. Selected rows support Delete, Ctrl+Z, Ctrl+C path copy, and one-place Up/Down moves. Multiple-row Delete offers the existing eight-second default-Yes playlist save prompt. Moves affect this session's order only.
- Automatic console-height changes repaint the first HUD Play line when transitioning to the next track.
- Dropping an audio file or folder onto the web page or native artwork/floating-lyrics window queues it through the active owner's queue bridge. Local browser drops can transfer bytes when browser path privacy hides the source path; remote uploads remain subject to the saved remote-upload control and existing size limits.
- On tray-only machines, the physical Pause key and Media Play/Pause key relay one pause toggle to the central player per press, including when the keys are reported together.
- On Windows, audio files of at most 64 MiB are read into memory and served through a seekable loopback source to the decoder. The original file handle is closed after the read, allowing a rename or deletion during playback when no other process holds it. Larger tracks retain disk-backed playback. Memory buffering does not remove unrelated locks held by tag readers, thumbnail providers, or antivirus tools.

Verification: focused V624 tests, relevant existing playlist/tray/queue tests, Python compilation, and bundled-source parity. FFprobe and FFmpeg successfully probed and sought in a one-second memory-backed WAV stream. Native shell drops and audible playback should also be checked on a running Windows desktop because automated tests cannot reproduce Explorer's window messages or audio output here.
