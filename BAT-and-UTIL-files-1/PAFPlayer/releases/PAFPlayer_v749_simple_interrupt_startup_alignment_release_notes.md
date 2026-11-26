# PAFPlayer V749 — simple interruption and startup alignment

Simple-mode Ctrl+C/Ctrl+Break now stops the decoder and unwinds for cleanup. Terminal restoration suppresses cursor-home, screen erase, cursor-color reset and full-screen reset behavior while an inline preview is active, including the session exception/finally paths. The renderer avoids rehoming to the first HUD row on interrupted simple teardown. Normal full-screen emergency handling retains its existing behavior.

Startup colon width follows the actual web-server label, placing the first colon directly after its port rather than padding to a fixed 50-cell column. MonkeyMote and resume rows share that width. Resume output separates the playlist filename, song filename and Resuming at timestamp into three rows, retaining italics only for filenames.

Validation covers the actual signal-handler function, emitted terminal bytes for both simple interrupt variants, normal-mode compatibility, simple splash regressions, simple-instance isolation, startup port-width alignment and resume formatting. Python syntax and release/source parity are also checked. No user audio files were changed.
