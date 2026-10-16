# PAFPlayer V510 — lock-screen identity, badges and activation diagnostics

Date: 2026-10-07. Player build: `2026-10-07-v510-lockscreen-identity-and-badges`.
Companion package: `510.0.0.5`.

**Not a confirmed lock-screen fix on DEMONA:** the package installs, but native
activation still fails with `0x80270254`, PID 0. No successful publication or
locked-screen visual verification is claimed.

The Windows package database contains the PAFPlayer family while its activation
cache omits it; the native family-lookup API returns zero packages. Calculator's
UWP app activates successfully with `EnableLUA=0`, disproving a blanket UAC
explanation. Targeted supported re-registration, maintenance and data-backed
reinstallation did not resolve the inconsistent cache. Its original cause is
unknown. UAC, Windows internal database contents and other apps were not changed.

Implemented: case-insensitive official-player verification; canonical Song/Artist
metadata; actual lyric tile text; playing/paused/idle/offline badges; expiry and
offline clearing; isolated desktop publisher with preserved package/app/config
IDs; default local server and explicit enable switch; an installer that requires
actual activation and publication instead of accepting registration as success.

Validation: 45 C# behavioral tests and 48 focused/related Python tests passed;
desktop compilation, MSIX packaging and EXE/MSIX signature verification passed.
The interactive installer correctly failed at real activation. These are focused
checks, not a claim that the entire historical 600+ test suite ran.

Only version/build labels changed in the main Python player. The frozen
`play_audio_file.py` was not changed. Existing release files were not overwritten.
Verified required backups were created before source/document replacement.

Full evidence, Windows limitations and manual checks:
[Windows lock-screen guide](../docs/windows-lock-screen.md).
Recovery data: `lockscreen/registration-recovery-20261007081230/app-data`.

No literal `C:\BAT` paths were created, modified, renamed, replaced or deleted.
The Windows-managed companion package was updated for the interactive account.
