"""Preserve the tested V514 package and document the unresolved visual check."""
from pathlib import Path
import hashlib
import json
import re
import zipfile
from backup_for_v510 import backup
import lockscreen_installer as installer

ROOT = Path(__file__).resolve().parents[1]
STEM = "PAFPlayer_v514_lockscreen_background_registration"
OUTPUTS = [ROOT / "releases" / (STEM + ".py"),
           ROOT / "releases" / (STEM + "_release_notes.md"),
           ROOT / "releases/PAFPlayer_v514_lockscreen_x64.msix",
           ROOT / "releases/PAFPlayer_v514_lockscreen_release_bundle.zip",
           ROOT / "docs" / (STEM + ".md"),
           ROOT / "releases" / (STEM + "_manifest.json")]

GUIDE = r'''# Windows 10 lock-screen status — V514

**Visible status remains unresolved.** The user confirmed a blank clock-and-date
lock screen with the first V514 candidate. The final self-contained package
`514.0.0.2` is installed and publishing successfully, but its visible result has
not been confirmed. Do not treat Settings selection, Appx status Ok, background
registration, or successful tile/badge API calls as visual proof.

The Windows picker, companion window and tray tooltip say **PAFPlayer Lock Screen
V514**. The package family and App ID are unchanged from V511–V513:
`ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2!App`.

## What V514 changes

- Registers a Windows 10 COM background task, as required for lock-screen
  presence. It requests background access and uses a recurring 15-minute timer;
  the desktop process still supplies live updates every five seconds.
- Uses a full MSIX package containing the executable and visual assets. Windows
  runs it from WindowsApps rather than an external workspace runtime directory.
  The build now uses complete MakeAppx validation, without `/nv`.
- Includes explicit COM launch permissions. A first candidate registered a task
  but COM activation failed with access denied. The corrected package actually
  launches and exposes `IBackgroundTask` successfully.
- Reports background access, registration and errors in its publication receipt.
  The installer requires both registration and actual COM activation, in addition
  to publication. These checks detect failures that Appx status Ok does not.

The background task uses the same read-only official-server verification as the
desktop publisher. It honors disabled settings, cancellation and server changes.
Disabling publishing or choosing **Exit and clear status** unregisters the task
and clears notifications. Closing the window hides it to the tray. No login
startup entry is installed. If the publisher crashes, the 15-minute task may
refresh status, but Windows schedules it and notifications still expire after
90 seconds; keep the desktop publisher running for continuous status.

Microsoft documents the [background-task requirement for lock-screen presence](https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-uap-lockscreen)
and the [Windows 10 COM task API](https://learn.microsoft.com/en-us/uwp/api/windows.applicationmodel.background.backgroundtaskbuilder.settaskentrypointclsid).
Meeting those requirements has not yet established visible rendering here.

## Installation and selection

From the project directory under the interactive Windows account:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py --check
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py
```

`--check` validates files and installed version without activating or publishing.
Normal installation verifies pinned MSIX/certificate hashes, the packaged EXE
hash, signer, manifest identity, display names and COM declaration. It upgrades
only the Recovery companion, activates it as the interactive user, verifies the
publication receipt and COM server, and starts the desktop publisher. No UAC
setting is changed. The existing PAFPlayerLocal certificate signs the package
and EXE; only its public certificate is included in the release.

Reopen Settings > Personalization > Lock screen. Select **PAFPlayer Lock Screen
V514** in both places:

- **Choose one app to show detailed status**: song, artist/playback state, lyric.
- **Choose which apps show quick status**: playing, paused, idle or offline badge.

The original unversioned PAFPlayer Lock Screen is a different package. Check the
name in each picker. V514 keeps the existing Recovery identity, LocalState JSON
settings and configuration keys `PAFPlayerServerUrl` and
`PAFPlayerLockScreenEnabled`. Saved disabled state and V510 JSON migration are
preserved. Earlier source/releases are retained.

## Read-only data and Windows boundaries

The default server is `http://127.0.0.1:666`. The companion only GETs
`/api/remote-tray/hello`, requiring `official=true`, a nonempty instance identity,
case-insensitive PAFPlayer program names in root and state, and matching nonempty
versions. It sends no playback commands. Redirects, proxy use, cookies and default
credentials are disabled. Requests time out after three seconds with a bounded
response. This HTTP identity assertion is not cryptographic authentication;
remote hosts must be on a trusted LAN.

`updated_at_epoch` is the last state-change time, not a heartbeat; an old timestamp
in a fresh verified response does not make a paused player offline. Unreachable
or invalid servers publish offline content without stale song/lyric text.

The wide tile supplies three explicit lock-screen text fields. Badge glyphs are
playing, paused, available (waiting), and unavailable (offline). Windows controls
visibility, placement and truncation. The status appears on the clock-and-date
lock screen, not the password/PIN sign-in screen. This is separate from the `.scr`
screensaver, wallpaper and media controls; it cannot draw arbitrary artwork over
the secure desktop.

The original package's activation failure was `0x80270254`
(`E_APPLICATION_NOT_REGISTERED`) and inconsistent family registration. The
Recovery identity activates with `EnableLUA=0`; a blanket claim that disabled UAC
prevents all these APIs would be incorrect. We have not established that UAC
causes the remaining blank display. No UAC, global notification/privacy setting,
Windows cache, or notification database was modified by this work.

Read-only diagnostics found running notification/background services and no
configured DisableLockScreenAppNotifications policy. Windows stores the tile and
badge, but internal lock-delivery flags remained zero for this app. Those flags
are unsupported internals, not a selection API or proof of a specific cause.
Two short ETW traces yielded no renderer events, including during a user-confirmed
lock/unlock cycle; both traces were stopped. Absence of events is inconclusive.

## Verification and remaining checks

Completed on Windows 10 with UAC still disabled:

- 47 C# checks for identity, metadata, Unicode, tile/badge payloads and GET-only
  networking; 52 related Python package/installer/tray checks (99 total).
- C# compilation, full MakeAppx validation, EXE/MSIX signature checks and pinned
  artifact checks. The final build/sign script was run in a fresh directory.
- Actual activation and publication under DEMONA\Claire, active console session
  1. Latest receipt verified the official player and submitted a playing badge.
- Background access AllowedSubjectToSystemPolicy, a registered refresh task, and
  actual COM launch with successful `IBackgroundTask` QueryInterface.

These are focused checks, not the entire main-player regression suite. Main-player
source differs from V513 only in three release constants. play_audio_file.py was
not modified. Automatic timer execution and visible rendering are separate from
COM activation; the timer's successful scheduled Run has not been demonstrated.

Manual procedure: keep PAFPlayer and the companion running, select the exact V514
name in both status slots, lock Windows yourself, and inspect the clock/date
screen before dismissing it. Verify current song and playing badge; use normal
player controls to test pause/resume, a timed lyric, and offline after closing the
player. Disable publishing to check clearing. The agent does not manipulate the
secure desktop. A blank screen must remain an open issue.

Reports are directly under `tests/reports`, including V514 publication receipts,
regressions, C# tests, build/signature checks and the 2026-10-08 interactive
installer check. Build with `lockscreen/build_desktop.ps1`; optional
`-SigningThumbprint` signs EXE and MSIX after verified backups. Run focused Python
checks with `lockscreen/run_regression_checks.py` and C# checks with
`lockscreen/test_desktop.ps1`. Do not overwrite an existing release artifact.

No literal `C:\BAT` paths changed.
'''

NOTES = r'''# PAFPlayer V514 — lock-screen background registration

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
'''

def write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data if isinstance(data, bytes) else data.encode("utf-8"))

def replace(path, text):
    backup(path)
    path.write_text(text, encoding="utf-8")

def main():
    for path in OUTPUTS:
        if path.exists():
            raise SystemExit("Release artifact exists: " + str(path))
    installer.validate_artifacts(*installer.artifacts(ROOT / "lockscreen"))
    source = (ROOT / "PAFPlayer.py").read_bytes()
    assert b"2026-10-07-v514-lockscreen-background-registration" in source
    replace(ROOT / "docs/windows-lock-screen.md", GUIDE)
    replace(ROOT / "lockscreen/README.md", """# PAFPlayer Lock Screen V514

Self-contained Windows 10 MSIX with a read-only desktop publisher, COM background
refresh registration and actual activation checks. Visible lock-screen status
remains unresolved; publication is not visual proof.

See the [guide and verification procedure](../docs/windows-lock-screen.md).
Use `python -B -X utf8 lockscreen_installer.py --check` for read-only validation;
omit `--check` to install and verify. The package in `dist/v514` contains the EXE;
an external runtime directory is no longer required. Select the versioned V514
entry in both Windows lock-screen status slots.

Build using `build_desktop.ps1` (optional `-SigningThumbprint` signs after verified
backups). Full MSIX validation is enabled. Run `run_regression_checks.py` and
`test_desktop.ps1`. Earlier UWP and sparse-package candidates are retained for
diagnosis. Never overwrite immutable releases or distribute a private key.
""")
    replace(ROOT / "docs/README.md", """# PAFPlayer documentation

Current release: **V514**. The Windows picker says **PAFPlayer Lock Screen V514**.
Native lock-screen rendering remains unresolved; activation/publication pass.

- [V514 release notes](../releases/PAFPlayer_v514_lockscreen_background_registration_release_notes.md)
- [Lock-screen guide and verification](windows-lock-screen.md)
- [V514 manual snapshot](PAFPlayer_v514_lockscreen_background_registration.md)
- [Main manual and historical coverage](../PAFPlayer.md)
- [Separate visual screensaver](visual-screensaver.md)
- [Playback controls](playback-controls.md)
- [Web configuration](web-config-playback.md)
""")
    manual = ROOT / "PAFPlayer.md"
    previous = manual.read_text(encoding="utf-8")
    marker = "## Historical comprehensive manual — V448"
    assert marker in previous
    header = """# PAFPlayer

## Current release — V514

**Source:** `PAFPlayer.py`  
**Snapshot:** `releases/PAFPlayer_v514_lockscreen_background_registration.py`  
**Build ID:** `2026-10-07-v514-lockscreen-background-registration`  
**Updated:** 2026-10-08

The lock-screen companion is now a self-contained MSIX with Windows 10 COM
background registration and real activation checks. Its picker name is
**PAFPlayer Lock Screen V514**. Native lock-screen rendering remains unresolved;
successful publication is not visual proof. Family/App ID and configuration keys
are preserved. Main-player changes are release constants only.

See the [guide and manual verification](docs/windows-lock-screen.md) and
[release notes](releases/PAFPlayer_v514_lockscreen_background_registration_release_notes.md).
The [visual screensaver](docs/visual-screensaver.md) remains separate.
UAC and play_audio_file.py were not changed. No literal C:\\BAT paths changed.

"""
    replace(manual, header + marker + previous.split(marker, 1)[1])
    write_new(OUTPUTS[0], source)
    write_new(OUTPUTS[1], NOTES)
    package = installer.artifacts(ROOT / "lockscreen")[0]
    write_new(OUTPUTS[2], package.read_bytes())
    snapshot = re.sub(r"\]\((?!https?:|#|/)([^)]+)\)", r"](../\1)", manual.read_text(encoding="utf-8"))
    write_new(OUTPUTS[4], snapshot)
    included = [ROOT / "PAFPlayer.py", manual, ROOT / "docs/windows-lock-screen.md", OUTPUTS[1], OUTPUTS[4],
                ROOT / "lockscreen/dist/PAFPlayerLockScreen_v505.cer", package]
    included += [ROOT / "lockscreen" / name for name in (
        "DesktopHost.cs", "DesktopBackground.cs", "DesktopHost.manifest", "DesktopPackage.appxmanifest",
        "StatusUpdater.cs", "StatusUpdaterTests.cs", "build_desktop.ps1", "test_desktop.ps1",
        "lockscreen_installer.py", "README.md")]
    included += sorted((ROOT / "lockscreen/Assets").glob("PAF*.png"))
    with zipfile.ZipFile(OUTPUTS[3], "x", zipfile.ZIP_DEFLATED) as archive:
        for path in included:
            archive.write(path, path.relative_to(ROOT).as_posix())
    manifest = {"version": "V514", "packageVersion": installer.PACKAGE_VERSION,
                "displayName": installer.PACKAGE_DISPLAY_NAME,
                "rendering": "unresolved; final self-contained candidate awaiting visual confirmation",
                "tests": {"csharp": 47, "python": 52}, "literalCBatChanges": [],
                "files": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in OUTPUTS[:-1]}}
    write_new(OUTPUTS[-1], json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
