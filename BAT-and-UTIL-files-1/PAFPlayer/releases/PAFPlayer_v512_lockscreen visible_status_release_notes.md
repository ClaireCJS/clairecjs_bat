# PAFPlayer V512 — visible native lock-screen status

The Recovery companion now activates and publishes to its own Windows identity.
The user confirmed visible lock-screen status after selecting **PAFPlayer Lock
Screen Recovery** in both slots. V512 retains this identity and fixes the
intermittent false-offline bug caused by treating the last state-change timestamp
as a heartbeat. It sends no playback commands and leaves UAC unchanged at 0.

The original identity has inconsistent Windows activation registration; the
parallel signed identity avoids that fault through supported Windows packaging.
The old package/data and configuration key names are preserved. New-family JSON
settings take priority, with read-only migration from V510 settings when absent.
The tile carries explicit lock-screen fields on its wide binding, and quick
status publishes playing, paused, idle and offline glyphs. The exact role of the
payload fields versus reselecting Recovery was not isolated visually.

47 C# checks and 50 related Python checks passed. Compilation, package build,
both signatures, installer checks and real interactive activation/publication
passed. Windows notification records contain real song and lyric updates.
Only release labels changed in PAFPlayer.py; play_audio_file.py was untouched.

Visual confirmation preceded the final V512 update. That update passed live
activation/publication with the same identity; paused/offline/disable/expiry
rendering and a separate final V512 lock/unlock remain manual checks. Keep the
companion running and retain lockscreen/dist/v512/runtime. The lock-screen
text/badge slots are separate from the screensaver and cannot host artwork layouts.

Use lockscreen/lockscreen_installer.py, not the MSIX alone. See the complete
[architecture, diagnosis and verification guide](../docs/windows-lock-screen.md).
The public signing certificate is included; no private key is distributed.
Existing release artifacts were not overwritten. Required replacement backups
were created and hash-verified. Obsolete, unexecuted internal-cache repair files
were recycled, not executed or permanently deleted.

No literal C:\BAT paths were created, modified, deleted, renamed or replaced.
