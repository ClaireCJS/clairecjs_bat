# PAFPlayer V516 — fix lock-screen launch from the music shell

The running player was correctly identified as V515, with publishing enabled.
Its automatic publisher launcher nevertheless displayed an installation error.
The signed 515.0.0.1 package was already installed and valid.

Reproducing the launch with that exact player's inherited environment exposed
the cause: PowerShell Add-Type's compiler rejected a 142043-byte environment
block (reported maximum 65535 bytes). A separate diagnostic shell had a smaller
environment, which is why the earlier live check passed.

V516 gives only the activation subprocess a small allowlisted Windows environment.
PAFPlayer's own environment, TCC configuration, playback and unrelated shell
variables are untouched. The installer uses the same isolation. Errors now show
Windows' actual failure message instead of always suggesting reinstallation.

Verification used the actual V515 process's environment and working directory.
The corrected child environment was approximately 1 KB. Managed launch,
official-player publication and graceful shutdown passed under DEMONA\Claire
in session 1, with UAC still disabled. 123 focused tests passed (72 Python,
51 C#), including oversized environment, parent preservation and error-reporting
regressions. Compilation, full MSIX validation and both signatures passed.

No main-player function/class body changed from V515: only the bundled helper
source and release constants changed. The prior 678-test V514/V515 comparison
is retained; those tests were not rerun for this isolated launch change.

The package is 516.0.0.0 and the picker says PAFPlayer Lock Screen V516. The
family, App ID and saved setting IDs are preserved. The running V515 playback
process was not restarted; the launch fix is loaded on the next V516 launch.
An independent publisher is available for the current session.

**The automatic-launch failure is reproduced and fixed. Native locked-screen
text/badge visibility is still unverified.** The prior rendering issue must not
be declared solved solely from notification publication.

No UAC settings, play_audio_file.py or literal C:\BAT paths changed. Earlier
release artifacts remain intact, and replacements have verified backups.

See the [guide and manual checks](../docs/windows-lock-screen.md).
