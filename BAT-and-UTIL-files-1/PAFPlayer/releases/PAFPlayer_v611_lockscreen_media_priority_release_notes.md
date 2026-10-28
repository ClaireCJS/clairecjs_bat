# PAFPlayer V611 — lock-screen media priority and text source

- The optional Windows media bridge reasserts PAFPlayer against a selected
  Chrome media session every five seconds while music plays, even if Chrome
  reports an active stream. It stops contesting Chrome when PAFPlayer is paused
  or stopped. It does not control or pause Chrome. Windows still makes the
  final right-panel selection, so the Nest card cannot be excluded absolutely.
- The lock-screen companion **source** adds 🎸 to the first line, 💿 to the
  album line, and `– PAFPlayer v611` to the end when version display is enabled.
  Long metadata retains the counter and version suffix. The installed signed
  V530 companion is unchanged; a newly signed package must be built and
  installed before these text changes appear on the actual lock screen.
- The remote tray continues relaying playback commands from client PCs. A
  client can already run the V530 lock-screen companion separately, point its
  server field at the verified central PAFPlayer host, and show left-side
  detailed status. Automatic tray management of that companion and local
  right-side media controls remain future work; managed mode currently
  requires loopback and a local owner process.

Focused Python and native C# tests cover Chrome selection policy, paused
behavior, detailed-status formatting, clipping, and the existing ownership
guards. Physical Windows lock-screen selection remains unverified.
