# PAFPlayer V513 — versioned lock-screen app name

The Windows app-picker entry now reads **PAFPlayer Lock Screen V513**. Both
manifest display names, the companion window, tray tooltip and selection
instructions include V513, so the active version can be distinguished from the
original unversioned app. The existing Recovery family/App ID and settings stay
the same. The installer validates the versioned display names.

Installed under the interactive Windows account: Windows' app catalog reports
the exact V513 name, and actual activation/official-player verification and
tile/badge submission passed. Fifty related Python checks passed; C# compilation,
MSIX packaging and both signatures passed. Status parsing/publication logic is
unchanged. Main-player changes are only the three release constants.

The user clarified that the native lock screen is still blank. Earlier claims
of visual success were mistaken; this naming release does not claim to resolve
that remaining issue. Close/reopen Settings and select **PAFPlayer Lock Screen
V513** in the top detailed-status and bottom quick-status pickers, then verify
the locked screen manually. Keep the companion running.

Use the supplied installer; retain `lockscreen/dist/v513/runtime`. UAC remains
unchanged. Required backups were verified and prior releases were not overwritten.
No literal C:\BAT paths changed. play_audio_file.py was not modified.

See the [updated guide](../docs/windows-lock-screen.md).
