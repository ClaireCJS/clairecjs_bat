"""One-time V510 documentation/release creation; refuse artifact overwrites."""
from pathlib import Path
import hashlib
import shutil
import zipfile
from backup_for_v510 import backup

ROOT = Path(__file__).resolve().parents[1]
STEM = "PAFPlayer_v510_lockscreen_identity_and_badges"

def replace(path, text):
    backup(path)
    path.write_text(text, encoding="utf-8")

def create(path, data):
    with path.open("xb") as stream:
        stream.write(data)

guide = r'''# Windows 10 lock-screen status — V510

**Status on DEMONA, 2026-10-07: activation is still blocked. This is not a
verified working lock-screen release on this computer. UAC remains disabled.**

## Diagnosis

The selected music-note icons in both Settings slots are correct. They prove
eligibility/selection, not that a publisher ran or submitted notifications.
`Get-AppxPackage` reports `Status: Ok`, but actual `IApplicationActivationManager`
activation returns `0x80270254` with PID 0, before application code executes.
The Windows SDK defines this as `E_APPLICATION_NOT_REGISTERED`; its separate
`E_UAC_DISABLED` code is `0x80270252`.

Read-only inspection found the PAFPlayer family in Windows' State Repository
database (ID 143), but its activation-cache data/index records are missing.
The documented `GetPackagesByPackageFamily` API returns zero packages for that
same family. Calculator's cache records exist, its native lookup returns one
package, and its UWP entry point `Calculator.App` activates successfully in the
same account, session and `EnableLUA=0` configuration (HRESULT 0, PID 677600).
This isolates a Windows registration inconsistency; it does not establish why
the cache originally became inconsistent. Disabled UAC is not a justified
blanket explanation, and changing it is not part of this solution.

Re-registering this app, running Windows' existing State Repository maintenance
task, and a targeted uninstall/reinstall with its app data copied and SHA-256
verified did not repair the missing family cache. Runtime changes alone did
not help: the original UWP and desktop identity packages fail activation, and
direct sparse-desktop launches report `0x80073D54` (no package identity).
No Windows internal database/registry repair, service restart, UAC change or
reboot was performed. Repeatedly reinstalling this same package is not a fix.

Evidence: `tests/reports/v510-registration-diagnosis-20261007082642.json` and
`tests/reports/v510-interactive-install-202610070817.txt`. App data was preserved
under `lockscreen/registration-recovery-20261007081230/app-data`.

## Architecture and implemented corrections

V510 supplies an independent .NET Framework desktop publisher plus a signed
Windows external-location (sparse) identity package. Windows documents this
identity mechanism for Windows 10 build 19041 onward. It preserves:

- Package name `ClaireCJS.PAFPlayer.LockScreen` and publisher `CN=PAFPlayerLocal`.
- Family `ClaireCJS.PAFPlayer.LockScreen_vz06efybxc4j2` and application ID `App`.
- The `PAFPlayerServerUrl` configuration key; saved UWP addresses migrate when
  the new settings file does not yet exist.

The running desktop publisher polls asynchronously every five seconds. It
has no playback module or playback-command path. This avoids UWP foreground
suspension, its 15-minute minimum timer interval, and AppContainer localhost
restrictions. It is a supported architecture candidate, **not a demonstrated
workaround for the damaged registration on DEMONA**. The old UWP sources remain
as reference; the V510 build entry point is `lockscreen/build_desktop.ps1`.

Each GET to `/api/remote-tray/hello` must verify `official=true`, a nonempty
instance identity, a case-insensitive PAFPlayer program name, matching root/state
versions, and a fresh timestamp when supplied. This accepts the real server's
`PAFplayer` spelling. Canonical `metadata.Artist` and `metadata.Song` fields are
used, with legacy names retained. Redirects, proxies, credentials and cookies
are disabled; timeout is three seconds and response size is capped. The existing
HTTP protocol is an official-instance assertion, not cryptographic server
authentication; local loopback is the default, and remote use needs a trusted LAN.

Detailed status uses actual legacy wide-tile text nodes for song, artist/state,
and the current lyric. Quick status publishes Windows' `playing`, `paused`,
`available` (idle) or `unavailable` (offline) badge. XML-invalid characters are
removed and truncation preserves Unicode pairs. Notifications expire after
90 seconds. An unavailable/unverified server clears old track information and
produces offline content. Tests verify these payloads, but Windows acceptance
and locked-screen rendering are still unverified on this PC.

The default server is `http://127.0.0.1:666`; installation/activation no longer
depends on opening a window and pressing Connect first. The settings window
has **Publish lock-screen status**, a server field, and **Save and refresh**.
Closing hides it to the tray. **Exit and clear status** ends the publisher.
Publishing is initially enabled when the companion is explicitly installed/run;
an existing disabled setting stays disabled. The setting key is
`PAFPlayerLockScreenEnabled`, stored with the server in
`%LOCALAPPDATA%\Packages\ClaireCJS.PAFPlayer.LockScreen_vz06efybxc4j2\LocalState\publisher-settings.json`.
Replacement settings files receive verified sibling backups. No login startup
entry is installed; launch the companion each Windows session when wanted.

## Install and verify

From the project directory, run:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py --check
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py
```

`--check` verifies files and current registration without launching or publishing.
Normal installation verifies pinned hashes and signing identity, asks before
trusting a new certificate, registers the signed package for the current user,
activates the actual app through the Windows activation manager, and requires
a receipt from the app with its own package identity and tile/badge publication.
Only then does it start the continuous publisher. It refuses downgrades.
`Get-AppxPackage` or Settings visibility alone cannot satisfy this gate.
On DEMONA it currently exits nonzero at activation with `0x80270254`.

The public development certificate is included; the private key is not. Keep
the `lockscreen/dist/v510/runtime` folder in place after installation because
the identity package references it. This is an x64 Windows 10 build; Windows 11
lock-screen behavior and Windows 10 ARM64 are not claimed supported.

After Windows registration is repaired and the activation gate passes, verify
manually in the interactive account:

1. Keep the official PAFPlayer server and companion running. Confirm its status
   names the current song and says tile/badge submission succeeded.
2. In Settings > Personalization > Lock screen, select PAFPlayer Lock Screen
   for detailed status and a quick-status slot. Re-select if an app repair
   removed the selection. Apps cannot select these slots themselves.
3. Lock using Win+L yourself. Check artist/song/current lyric plus playing badge.
   Pause and resume using your usual player controls and check the paused/playing
   badges. The companion itself sends no playback commands.
4. Stop PAFPlayer normally; within the polling delay the companion should show
   offline status. Start PAFPlayer again and confirm it recovers.
5. Disable publishing in the companion and confirm both notifications clear.
   Close/exit it and confirm content does not remain beyond its expiry.

## Platform boundaries

Microsoft's tile/badge APIs update the calling app or another app **in the same
package**. An arbitrary desktop process cannot use a foreign AUMID as a
supported way to take over the selected status slot. A sparse package still
needs working Windows identity registration, so it cannot bypass this machine's
broken family lookup. UWP's general ability to activate with UAC disabled was
demonstrated by Calculator; this PAFPlayer UWP package cannot be evaluated past
the current Deployment failure. No claim that UAC makes it inherently impossible
is supported by the evidence.

Windows controls lock-screen rendering, privacy choices, truncation and update
timing. The status slots are text/badge surfaces, not artwork or interactive
karaoke. SMTC media cards, desktop wallpaper, floating lyric windows, and the
optional `.scr` screensaver are separate features; none replaces or draws over
the secure native lock screen. This work did not modify their behavior.

Locked-screen appearance was not visually verified. The supplied Settings
screenshot confirms both selections; it is not a screenshot of rendered status.
Desktop automation could not capture Settings (`FrameArrived timed out`), and
no secure-lock-screen interaction was attempted.

## Checks

- 45 C# behavioral checks passed, including real WinRT JSON/XML APIs and loopback
  HTTP fixtures for verification, redirects, failure handling and read-only GET.
- 48 relevant Python checks passed: current installer, immutable V505/V509
  packages, official-instance ownership, remote tray/status and local tray behavior.
- Desktop C# compilation and fresh MSIX packaging passed; both the EXE and MSIX
  passed `signtool verify /pa /v` with zero errors/warnings.
- Real interactive registration succeeded; activation/publication gate failed
  as described above. This is deliberately reported as a failure.

Run `lockscreen/test_desktop.ps1` for the C# suite and
`python -B -X utf8 lockscreen/run_regression_checks.py` for focused Python checks.
Fixtures are isolated and retained; reports go directly under `tests/reports`.
`capture_registration_diagnostics.py` reads the package database/cache and attempts
a verification activation; it performs no repair or database/registry writes.

## Microsoft references

- [External-location package identity](https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/grant-identity-to-nonpackaged-apps)
- [Lock-screen manifest contract](https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-uap-lockscreen)
- [Tile ownership requirement](https://learn.microsoft.com/en-us/uwp/api/windows.ui.notifications.tileupdatemanager.createtileupdaterforapplication)
- [Badge ownership requirement](https://learn.microsoft.com/en-us/uwp/api/windows.ui.notifications.badgeupdatemanager.createbadgeupdaterforapplication)
- [Package-family lookup](https://learn.microsoft.com/en-us/windows/win32/api/appmodel/nf-appmodel-getpackagesbypackagefamily)
- [App activation troubleshooting](https://learn.microsoft.com/en-us/troubleshoot/windows-client/shell-experience/modern-inbox-store-apps-troubleshooting-guidance)
- [Repair versus reset](https://learn.microsoft.com/en-us/windows/msix/desktop/managing-your-msix-reset-and-repair)
'''

readme = '''# PAFPlayer Lock Screen — V510

**Activation remains blocked on DEMONA. Do not treat this release as a verified
working lock-screen display.** See the [diagnosis, architecture, configuration,
verification procedure and Microsoft references](../docs/windows-lock-screen.md).

The V510 desktop publisher preserves the existing lock-screen package/app IDs.
It reads the official player's local status API, verifies its identity on every
poll, publishes real tile text plus playing/paused/offline badges, and offers an
explicit publishing switch. It sends no playback commands and defaults to
`http://127.0.0.1:666`. UAC is neither required by the installer nor changed.

Run `python -B -X utf8 lockscreen_installer.py --check` for a read-only artifact
and registration check. Omit `--check` to install and test actual activation and
publication. The installed identity points at `dist/v510/runtime`; keep it there.
The current PC fails the activation gate with `0x80270254`, despite healthy
package enumeration. Calculator UWP activation succeeds with the same UAC setting.

Build with `build_desktop.ps1` using .NET Framework's x64 C# compiler and Windows
SDK 26100. The script creates a unique output folder and refuses overwrite.
It uses the documented external-location manifest and MakeAppx `/nv` because
the EXE is outside the identity package. Sign both EXE and MSIX with the matching
publisher certificate after making verified sibling backups; never distribute
the private key. Update version and pinned installer hashes for a new release.

`StatusUpdaterTests.cs` / `test_desktop.ps1` test the actual status implementation.
`run_regression_checks.py` runs related Python tests with isolated, retained
fixtures. Results go directly to `../tests/reports`.

`App.xaml`, `MainPage.xaml`, `BackgroundRefresh.cs`, `Package.appxmanifest`, and
the UWP projects are retained as historical/reference source, not the V510 build.
The V509 MSIX and older releases are preserved. Diagnostic candidates and the
verified registration-recovery data are retained locally for investigation.
`repair_registration.ps1` is a specific recovery experiment, not a routine
installer step: recreating registration already failed to repair this PC's cache.
Do not run it repeatedly expecting a different result.
'''

notes = '''# PAFPlayer V510 — lock-screen identity, badges and activation diagnostics

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

No literal `C:\\BAT` paths were created, modified, renamed, replaced or deleted.
The Windows-managed companion package was updated for the interactive account.
'''

replace(ROOT / "docs" / "windows-lock-screen.md", guide)
replace(ROOT / "lockscreen" / "README.md", readme)
replace(ROOT / "docs" / "README.md", '''# PAFPlayer documentation

Current source release: **V510**. The lock-screen companion is still blocked by
Windows activation on DEMONA; its Settings icons do not establish working status.

- [V510 release notes](../releases/PAFPlayer_v510_lockscreen_identity_and_badges_release_notes.md)
- [Windows lock-screen architecture, diagnosis and manual checks](windows-lock-screen.md)
- [Main manual and historical coverage](../PAFPlayer.md)
- [Visual screensaver (separate from the native lock screen)](visual-screensaver.md)
- [Playback controls](playback-controls.md)
- [Web configuration](web-config-playback.md)

Sources, releases, docs and reports are maintained under
`C:\\codex\\clairevironment\\bat\\PAFPlayer`. V510 did not modify literal `C:\\BAT` files.
''')
manual = ROOT / "PAFPlayer.md"
old = manual.read_text(encoding="utf-8")
historical = old[old.index("## Historical comprehensive manual — V448"):]
replace(manual, '''# PAFPlayer

## Current source release — V510

**Current sandbox source:** `PAFPlayer.py`  
**Numbered snapshot:** `releases/PAFPlayer_v510_lockscreen_identity_and_badges.py`  
**Build ID:** `2026-10-07-v510-lockscreen-identity-and-badges`  
**Updated:** 2026-10-07

V510 repairs lock-screen status parsing, adds badge publication, and supplies an
isolated desktop publisher with the existing Windows identity. **The companion
still fails native activation on DEMONA; this is not a verified working display.**
See the [diagnosis and manual verification guide](docs/windows-lock-screen.md)
and [release notes](releases/PAFPlayer_v510_lockscreen_identity_and_badges_release_notes.md).
The Settings selections are correct. UAC was not changed. Main-player playback
behavior and the frozen `play_audio_file.py` are unchanged by this release.

The `.scr` screensaver is separate: [screensaver guide](docs/visual-screensaver.md).
The comprehensive manual below is historical coverage; current updates live
under `docs` and `releases`.

''' + historical)
create(ROOT / "docs" / (STEM + ".md"), (ROOT / "PAFPlayer.md").read_bytes())
create(ROOT / "releases" / (STEM + ".py"), (ROOT / "PAFPlayer.py").read_bytes())
create(ROOT / "releases" / (STEM + "_release_notes.md"), notes.encode("utf-8"))
package = ROOT / "lockscreen" / "dist" / "v510" / "PAFPlayerLockScreen_v510_x64.msix"
create(ROOT / "releases" / "PAFPlayer_v510_lockscreen_x64.msix", package.read_bytes())
bundle = ROOT / "releases" / "PAFPlayer_v510_lockscreen_release_bundle.zip"
files = [ROOT / "lockscreen" / "lockscreen_installer.py", ROOT / "lockscreen" / "README.md",
         ROOT / "lockscreen" / "dist" / "PAFPlayerLockScreen_v505.cer", ROOT / "docs" / "windows-lock-screen.md"]
files += [p for p in (ROOT / "lockscreen" / "dist" / "v510").rglob("*") if p.is_file()]
with zipfile.ZipFile(bundle, "x", zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(bundle) as archive:
    assert archive.testzip() is None
    for path in files:
        assert hashlib.sha256(archive.read(path.relative_to(ROOT).as_posix())).digest() == hashlib.sha256(path.read_bytes()).digest()
assert (ROOT / "releases" / (STEM + ".py")).read_bytes() == (ROOT / "PAFPlayer.py").read_bytes()
print("Created V510 source snapshot, versioned manual, signed package copy, release notes and verified bundle.")
