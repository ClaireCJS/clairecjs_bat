# V559 instant console break

V559 separates emergency console interruption from PAFPlayer's orderly shutdown.
Ctrl+C and Ctrl+Break now perform only the work required for a clean, immediate
return to the shell:

1. Reset ANSI rendition, the DEC character set, line width, wrapping, cursor
   visibility, palette state, and the PAFPlayer viewport.
2. Kill the active decoder process without waiting for process confirmation.
3. Exit PAFPlayer directly with status 130.

This deliberately bypasses tray, web-server, media-session, workflow, and GUI
thread joins. Windows reclaims those process-owned resources. Normal quit actions
still use the orderly cleanup path so preferences and application state continue
to close normally.
