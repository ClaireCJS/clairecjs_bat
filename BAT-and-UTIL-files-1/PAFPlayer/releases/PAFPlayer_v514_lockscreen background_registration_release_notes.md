# PAFPlayer V514 — lock-screen background registration

Added the Windows 10 COM background refresh registration and its launch
permissions. The installer now verifies real COM activation as well as the
official-player tile/badge publication receipt. The final `514.0.0.2` MSIX contains
the executable and images; Windows no longer relies on an external workspace
runtime. The display name remains **PAFPlayer Lock Screen V514**.

**The blank native lock screen is not claimed fixed.** The first V514 candidate
was still blank in the user's visual check. The self-contained final package is
installed and publishes successfully, but visible text/badges remain unconfirmed.
The precise cause of the remaining rendering failure is not established.

99 focused checks passed: 47 C# and 52 Python. Compilation, full package
validation, both signatures, interactive activation/publication, background
registration/access and actual COM interface activation passed. Scheduled timer
execution and the final locked-screen appearance are not verified by these tests.

Family/App ID and configuration keys are preserved. The companion reads only
the verified official PAFPlayer endpoint and sends no playback commands. Main
player changes are three release constants only. UAC remains disabled and
unchanged; play_audio_file.py was not modified. All required replacements had
verified backups; earlier release artifacts were preserved.

No literal C:\BAT paths were created, modified or deleted.

See the [guide and manual checks](../docs/windows-lock-screen.md).
