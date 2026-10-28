"""Publish V513 without overwriting any existing release artifact."""
from pathlib import Path
import hashlib
import json
import re
import zipfile
from backup_for_v510 import backup
import lockscreen_installer as installer

ROOT = Path(__file__).resolve().parents[1]
STEM = 'PAFPlayer_v513_lockscreen_versioned_name'
OUTPUTS = [ROOT/'releases'/(STEM+'.py'), ROOT/'releases'/(STEM+'_release_notes.md'),
           ROOT/'releases/PAFPlayer_v513_lockscreen_x64.msix',
           ROOT/'releases/PAFPlayer_v513_lockscreen_release_bundle.zip',
           ROOT/'docs'/(STEM+'.md'), ROOT/'releases'/(STEM+'_manifest.json')]

GUIDE = r'''# Windows 10 lock-screen status — V513

The Windows app-picker name is now **PAFPlayer Lock Screen V513**. The package
display name, application display name, window title, tray tooltip and setup
instructions all include the version. Windows' installed manifest and Start-app
catalog were read back and report this exact name.

**Actual locked-screen rendering remains unresolved.** The user clarified that
nothing appears there. Earlier V512 documentation interpreted an intermediate
reply as visual confirmation; that interpretation is withdrawn. Activation and
notification publication succeed, but they are not proof of visible status.
V513 is a naming update, not a claim to have fixed the remaining rendering issue.

## Select the versioned entry

Close and reopen Windows Settings if it was already open during installation.
Under Settings > Personalization > Lock screen, choose **PAFPlayer Lock Screen
V513** in BOTH places:

- Top, **Choose one app to show detailed status**: song, artist and current lyric.
- Bottom, **Choose which apps show quick status**: playing/paused/offline badge.

Open each picker and check the name rather than relying on the music-note icon.
The original unversioned **PAFPlayer Lock Screen** package is a different app.
V513 upgrades the existing Recovery package; it does not create another family.
Keep its companion running. Closing the window hides it to the tray; **Exit and
clear status** stops it. No login startup entry is installed.

## Installation and compatibility

From the project directory under the interactive Windows account:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py --check
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py
```

`--check` is read-only. Normal installation verifies pinned hashes/signing
identity, registers the package, requires a real activation/publication receipt,
and starts the publisher. It may close only its existing Recovery process during
upgrade. Use the installer, not the MSIX alone, and keep
`lockscreen/dist/v513/runtime` in place. Both EXE and MSIX are signed with the
existing PAFPlayerLocal certificate; only the public certificate is distributed.

Stable package name: `ClaireCJS.PAFPlayer.LockScreen.Recovery`; family:
`ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2`; application ID: `App`.
Package version is `513.0.0.0`. The unchanged configuration keys are
`PAFPlayerServerUrl` and `PAFPlayerLockScreenEnabled`. Their JSON settings remain
under the same package LocalState directory; the V510 JSON migration remains.
Saved disabled state is preserved. No UAC setting is changed.

## Publisher behavior and limits

The separate .NET Framework desktop process polls asynchronously every five
seconds, reading only GET `/api/remote-tray/hello`. It verifies `official=true`,
nonempty instance identity, case-insensitive PAFPlayer root/state program names,
and matching versions on every response. The default is `http://127.0.0.1:666`.
Redirects, proxies, cookies and default credentials are disabled; timeout is
three seconds and response size is bounded. No playback commands are sent.
This existing HTTP identity assertion is not cryptographic authentication;
remote use requires a trusted LAN.

V512's timestamp correction remains: `updated_at_epoch` dates a state change,
not a heartbeat. A live official response is not rejected just because playback
or pause state has stayed unchanged. Invalid or unreachable servers produce
offline content without retaining an old song.

The wide tile contains song, artist/playback state and current timed lyric,
with explicit lock-screen fields. Badges are playing, paused, available (idle)
or unavailable (offline). Updates expire after 90 seconds; disabling/exiting
clears them. Windows controls rendering, truncation, placement and privacy.
Settings selection and successful API calls alone cannot verify the lock screen.
Internal notification-database flags are not a supported selection API.

The original package failed before startup with `0x80270254`
(`E_APPLICATION_NOT_REGISTERED`) despite Appx status Ok. Read-only inspection
found inconsistent family registration. Reinstallation did not resolve it;
the parallel Recovery identity activated successfully with EnableLUA=0.
The old package/data and previous releases remain preserved. No Windows internal
cache patch, UAC change or reboot was used. The cause of the original corruption
is unknown; the remaining rendering issue is still under investigation.

This publisher targets Windows 10 x64, builds 19041–19045. Text/badge status is
separate from the `.scr` screensaver, wallpaper, SMTC and floating lyric windows.
It cannot host album-art layouts or draw over the secure native lock screen.

## Verification

V513 passed 50 related Python checks, C# compilation, MSIX packaging, EXE/MSIX
signature verification, and actual interactive installation/activation/publication.
The installed Windows app catalog reports **PAFPlayer Lock Screen V513**. The
installer also validates both versioned manifest display names. StatusUpdater.cs
is unchanged from V512's 47-test C# run; that suite was not rerun for this label
change. Main-player changes are only three release constants.

For manual checking, select the exact V513 name in both slots, keep the official
player and companion running, and lock Windows yourself. Check current song,
available lyric and playing badge. Then use ordinary playback controls to test
pause/resume; close the player normally to test offline; disable the companion
to test clearing. Do not treat a successful publication receipt as visual proof.

Reports are directly under `tests/reports`, including the V513 regressions,
interactive installation, publication receipt and final release validation.
Build with `lockscreen/build_desktop.ps1`; run related Python checks with
`python -B -X utf8 lockscreen/run_regression_checks.py`. For future releases,
update both manifest display names alongside the version and installer constant.

[Microsoft package identity documentation](https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/grant-identity-to-nonpackaged-apps)
and [tile content documentation](https://learn.microsoft.com/en-us/windows/uwp/launch-resume/tile-schema)
describe the underlying interfaces. They do not establish visible rendering on
this computer.

No literal `C:\BAT` paths were changed. `play_audio_file.py` was not modified.
'''

NOTES = r'''# PAFPlayer V513 — versioned lock-screen app name

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
'''

def write_new(path, data):
    with path.open('xb') as stream:
        stream.write(data if isinstance(data, bytes) else data.encode('utf-8'))

def replace(path, data):
    backup(path)
    path.write_text(data, encoding='utf-8')

def main():
    for path in OUTPUTS:
        if path.exists(): raise SystemExit('Release artifact exists: '+str(path))
    installer.validate_artifacts(*installer.artifacts(ROOT/'lockscreen'))
    source=(ROOT/'PAFPlayer.py').read_bytes()
    assert b'2026-10-07-v513-lockscreen-versioned-name' in source
    replace(ROOT/'docs/windows-lock-screen.md',GUIDE)
    replace(ROOT/'lockscreen/README.md', '''# PAFPlayer Lock Screen V513

The app picker, window title and tray tooltip now show **PAFPlayer Lock Screen
V513**. It upgrades the existing Recovery identity and preserves its settings.
Actual locked-screen rendering remains unresolved; API publication works.

See the [current guide and manual checks](../docs/windows-lock-screen.md).
Use `python -B -X utf8 lockscreen_installer.py --check` for a read-only check;
omit `--check` to install, activate and run the publisher. Retain
`dist/v513/runtime`. Select the exact V513 name in BOTH lock-screen Settings
pickers. Reopen Settings if it still displays a cached older name.

Build with `build_desktop.ps1`; use `run_regression_checks.py` for related Python
checks and `test_desktop.ps1` for the unchanged C# status tests. Make verified
backups before signing EXE/MSIX; pin hashes and both display names in the installer.
Never overwrite a release artifact or distribute the private signing key.
The older UWP projects and build candidates are historical reference.
''')
    replace(ROOT/'docs/README.md', '''# PAFPlayer documentation

Current release: **V513**, with the versioned app-picker name **PAFPlayer Lock
Screen V513**. The remaining locked-screen rendering problem is unresolved.

- [V513 release notes](../releases/PAFPlayer_v513_lockscreen_versioned_name_release_notes.md)
- [Lock-screen guide and manual verification](windows-lock-screen.md)
- [V513 manual snapshot](PAFPlayer_v513_lockscreen_versioned_name.md)
- [Main manual and historical coverage](../PAFPlayer.md)
- [Separate visual screensaver](visual-screensaver.md)
- [Playback controls](playback-controls.md)
- [Web configuration](web-config-playback.md)

No literal C:\\BAT paths changed.
''')
    manual=ROOT/'PAFPlayer.md'
    previous=manual.read_text(encoding='utf-8')
    marker='## Historical comprehensive manual — V448'
    assert marker in previous
    header='''# PAFPlayer

## Current release — V513

**Source:** `PAFPlayer.py`  
**Snapshot:** `releases/PAFPlayer_v513_lockscreen_versioned_name.py`  
**Build ID:** `2026-10-07-v513-lockscreen-versioned-name`  
**Updated:** 2026-10-07

The Windows app-picker name is **PAFPlayer Lock Screen V513**, also shown in the
window title and tray tooltip. The Recovery identity and configuration IDs stay
the same. Select the exact V513 name in both Lock screen Settings slots.
Actual locked-screen rendering remains unresolved; activation/publication pass.
Main-player changes are release labels only; play_audio_file.py is unchanged.

See the [current guide](docs/windows-lock-screen.md) and
[release notes](releases/PAFPlayer_v513_lockscreen_versioned_name_release_notes.md).
The [visual screensaver](docs/visual-screensaver.md) remains a separate feature.
No literal C:\\BAT paths changed.

'''
    replace(manual,header+marker+previous.split(marker,1)[1])
    write_new(OUTPUTS[0],source)
    write_new(OUTPUTS[1],NOTES)
    write_new(OUTPUTS[2],(ROOT/'lockscreen/dist/v513/PAFPlayerLockScreen_v513_x64.msix').read_bytes())
    # This snapshot is one directory deeper than the main manual.
    snapshot=re.sub(r'\]\((?!https?:|#|/)([^)]+)\)',r'](../\1)',manual.read_text(encoding='utf-8'))
    write_new(OUTPUTS[4],snapshot)
    included=[ROOT/'PAFPlayer.py',manual,ROOT/'docs/windows-lock-screen.md',OUTPUTS[1],OUTPUTS[4],
              ROOT/'lockscreen/dist/PAFPlayerLockScreen_v505.cer']
    included += [ROOT/'lockscreen'/name for name in ('DesktopHost.cs','DesktopHost.manifest',
        'DesktopPackage.appxmanifest','StatusUpdater.cs','StatusUpdaterTests.cs','build_desktop.ps1',
        'test_desktop.ps1','lockscreen_installer.py','README.md')]
    included += sorted((ROOT/'lockscreen/Assets').glob('PAF*.png'))
    included += sorted(p for p in (ROOT/'lockscreen/dist/v513').rglob('*') if p.is_file())
    with zipfile.ZipFile(OUTPUTS[3],'x',zipfile.ZIP_DEFLATED) as z:
        for path in included: z.write(path,path.relative_to(ROOT).as_posix())
    manifest={'version':'V513','packageVersion':'513.0.0.0','displayName':installer.PACKAGE_DISPLAY_NAME,
              'lockScreenRendering':'unresolved per user; naming and publication verified',
              'pythonTests':50,'literalCBatChanges':[],
              'files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in OUTPUTS[:-1]}}
    write_new(OUTPUTS[-1],json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__': main()
