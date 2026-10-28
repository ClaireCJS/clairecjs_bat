"""Create the immutable V512 release; refuse any existing release destination."""
from pathlib import Path
import hashlib
import json
import zipfile
from backup_for_v510 import backup

ROOT = Path(__file__).resolve().parents[1]
STEM = "PAFPlayer_v512_lockscreen_visible_status"
RELEASE = ROOT / "releases"
DESTINATIONS = [RELEASE / (STEM + ".py"), RELEASE / (STEM + "_release_notes.md"),
                RELEASE / "PAFPlayer_v512_lockscreen_x64.msix",
                RELEASE / "PAFPlayer_v512_lockscreen_release_bundle.zip",
                RELEASE / (STEM + "_manifest.json"), ROOT / "docs" / (STEM + ".md")]

GUIDE = r'''# Windows 10 lock-screen status — V512

On 2026-10-07 the user confirmed native lock-screen status became visible after
selecting **PAFPlayer Lock Screen Recovery** in both Windows Settings slots.
The subsequent V512 update keeps that same Recovery identity and fixes false
offline reports. Its real activation, official-player verification, tile/badge
publication and continuously delivered lyric updates passed under DEMONA\Claire,
session 1, with **EnableLUA=0 unchanged**. V512 was not separately visually
rechecked after that update; the visual confirmation applies to the Recovery
publisher immediately before it. No secure-lock-screen automation was attempted.

## What failed, and what resolved it

The original family `ClaireCJS.PAFPlayer.LockScreen_vz06efybxc4j2` was installed
but absent from Windows' activation-cache lookup. Activation failed before the
process started with `0x80270254` (`E_APPLICATION_NOT_REGISTERED`), while
`Get-AppxPackage` reported Ok. The SDK's separate UAC-disabled error is
`0x80270252`. Calculator activated in the same account with UAC disabled.
This establishes a registration inconsistency, not what originally caused it.

Re-registering and reinstalling the original identity did not repair that
inconsistency. The supported solution is a signed external-location package
with the parallel **Recovery** identity. It activated and published successfully.
The original package and its saved data remain available. A temporary SYSTEM
cache-edit experiment was rejected by automatic approval review and never ran;
its obsolete script and plan were recycled. Windows internals were not patched.

Windows treats Recovery as a separate app: the older music-note selection does
not select it. Open each picker and choose the full Recovery name. The user
reported visible status after doing that. Explicit detailed-status fields were
also added on the wide tile binding, following the Windows Community Toolkit
7.1.2 serializer, alongside legacy text nodes. The separate effect of those
fields versus reselecting Recovery was not isolated in a visual A/B test.

An additional parser bug incorrectly treated `updated_at_epoch` as a heartbeat.
It actually dates the last state publication. A live official response with an
old timestamp was rejected after 30 seconds, causing intermittent offline
content during songs or pauses. V512 verifies each fresh HTTP response and its
official-instance identity without rejecting an unchanged state timestamp.
Unreachable or invalid servers still produce offline status.

Internal `wpndatabase.db` flags are diagnostic data, not a supported selection
API: `s:lock:tile` and `s:lock:badge` remained zero despite the user's visual
confirmation. Do not use them to decide that Settings selection failed. The
receipt's public `TileUpdater.Setting` was Enabled; actual Windows notification
records contained the current song, lyric and playing badge.

## Architecture and compatibility

- Independent .NET Framework desktop process; asynchronous polling every five
  seconds, with at most one refresh in flight. Playback code is not loaded.
- Signed Windows external-location identity, supported from Windows 10 build
  19041. Package `ClaireCJS.PAFPlayer.LockScreen.Recovery`, family
  `ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2`, application ID `App`,
  publisher `CN=PAFPlayerLocal`, package version `512.0.0.0`.
- Only GET `/api/remote-tray/hello`. Every response must assert `official=true`,
  a nonempty instance identity, case-insensitive PAFPlayer root/state program
  names, and matching nonempty versions. This accepts `PAFplayer`. Canonical
  `metadata.Artist` / `metadata.Song` and legacy metadata names are supported.
- Redirects, proxies, cookies and default credentials are disabled; requests
  time out after three seconds with a 2 MiB response cap. This existing HTTP
  protocol is an official-instance assertion, not cryptographic authentication.
  Default to local loopback; any remote server must be on a trusted LAN.
- Detailed status carries song, artist/playback state and current timed lyric.
  Quick status uses `playing`, `paused`, `available` (idle), `unavailable`
  (offline). Missing/unverified players cannot leave stale song metadata.
- XML text is escaped, invalid characters removed and Unicode pairs preserved.
  Tile updates replace the same `PAFStatus` tag. Both notifications expire after
  90 seconds; disabling or exiting explicitly clears them.

Configuration keys remain `PAFPlayerServerUrl` and `PAFPlayerLockScreenEnabled`.
The default server is `http://127.0.0.1:666`. The Recovery settings file lives in
`%LOCALAPPDATA%\Packages\ClaireCJS.PAFPlayer.LockScreen.Recovery_vz06efybxc4j2\LocalState\publisher-settings.json`.
When absent, the publisher reads the original family's V510 JSON settings if
present, without editing that file. New JSON takes precedence; the local-settings
server fallback is preserved. Disabled settings stay disabled. Settings writes
make and hash-verify the required sibling backup first, preserving collisions.

The window has **Publish lock-screen status**, a server field and **Save and
refresh**. Closing hides it to the tray. **Exit and clear status** stops it.
Publishing is initially enabled when explicitly installed/launched. No startup
entry is added: launch Recovery from Start each Windows session when wanted.

## Install and manual verification

From the PAFPlayer project directory, under the interactive Windows account:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py --check
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py
```

The first command checks pinned artifacts/signing identity and registration
without launching or publishing. Normal installation requires an actual
activation/publication receipt before launching the continuous publisher. It
refuses downgrades, retains the original package, and may close only the existing
Recovery publisher during an upgrade. Certificate trust needs consent only if
the supplied public development certificate is not already trusted. The private
key is never distributed. UAC is read for diagnostics and never modified.

Keep `lockscreen/dist/v512/runtime` in place: the installed package references
that external directory. Installing the MSIX alone is insufficient; use the
installer with the supplied runtime. The running player need not be restarted
for the companion update.

1. Keep PAFPlayer's official web server and Recovery running. Its window should
   name the current song and report tile/badge submission, not an error.
2. In Settings > Personalization > Lock screen, explicitly select **PAFPlayer
   Lock Screen Recovery** for detailed status AND one quick-status slot. Open
   the picker to check the name; the old and new music-note icons look alike.
3. Lock Windows yourself. Check title, artist, current lyric when available,
   and the playing badge. Wait for a lyric/track update.
4. Use normal player controls to pause/resume and confirm the badge changes.
   Leave a song or pause unchanged for over 30 seconds: it must not become
   offline just because its state timestamp is old.
5. Close PAFPlayer normally and check offline status within the polling/request
   delay (up to about eight seconds). Restart it and check recovery.
6. Disable publishing and save: both notifications should clear. Re-enable to
   resume. Exiting clears them; after a crash they expire within 90 seconds.

Playing visibility was confirmed by the user. Paused/offline/disable/expiry
behavior has automated coverage but has not all been visually checked on the
locked desktop. The final V512 build passed actual activation/publication, not
a second user lock/unlock check.

## Windows boundaries

The Windows notification APIs can update the caller or another app in the same
package, not an arbitrary foreign selected identity. Recovery therefore needs
its own one-time user selection. No supported API silently chooses the user's
lock-screen slots. Windows owns placement, truncation, privacy and timing.
This build targets Windows 10 x64 build 19041–19045; Windows 11 status surfaces
and ARM64 are not claimed supported.

These text/badge slots cannot host album-art layouts or an interactive karaoke
window. SMTC cards, wallpaper, the optional `.scr` screensaver and floating lyrics
are separate features. Nothing replaces or paints over Windows' secure desktop.
The desktop publisher runs independently instead of depending on a suspended
UWP window or a 15-minute UWP timer. UAC-disabled operation is demonstrated here;
there is no claim that every UWP application works in every such configuration.

## Checks and evidence

- 47 focused C# tests passed, including real WinRT JSON/XML, read-only HTTP
  requests, old-state responses, invalid identities, redirects, text and badges.
- 50 related Python tests passed: installer, historical package contracts,
  ownership, remote status, tray and wallpaper isolation.
- Desktop compilation, fresh MSIX build, and `signtool verify /pa` passed for
  both EXE and package. Actual interactive upgrade/activation passed with UAC 0.
- Windows retained and delivered the current song, timed lyric and playing
  badge. Main-player changes are only three release-label constants.

Reports are directly under `tests/reports`:
`v512-status-updater-20261007134955.txt`,
`v512-regressions-20261007135032.txt`,
`v512-interactive-install-20261007135051.txt`,
`v512-publication-96b7ec3ea52848f9a1a6be129059f156.json`, and
`v512-windows-delivery-20261007135110.json`.
The V510 registration diagnosis and earlier immutable releases remain preserved.

Build using `lockscreen/build_desktop.ps1`; it creates a fresh directory and
refuses overwrite. Sign only after making verified backups, then pin the new
hashes in the installer. Run `lockscreen/test_desktop.ps1` and
`python -B -X utf8 lockscreen/run_regression_checks.py`. This is a focused set,
not a claim to have run the entire historical player suite.

## Microsoft references

- [External-location identity](https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/grant-identity-to-nonpackaged-apps)
- [Lock-screen manifest](https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-uap-lockscreen)
- [Detailed-status tile fields](https://learn.microsoft.com/en-us/windows/uwp/launch-resume/tile-schema)
- [Toolkit 7.1.2 serialization](https://github.com/CommunityToolkit/WindowsCommunityToolkit/blob/v7.1.2/Microsoft.Toolkit.Uwp.Notifications/Tiles/Elements/Element_TileBinding.cs)
- [Tile API ownership](https://learn.microsoft.com/en-us/uwp/api/windows.ui.notifications.tileupdatemanager.createtileupdaterforapplication)
- [Badge API ownership](https://learn.microsoft.com/en-us/uwp/api/windows.ui.notifications.badgeupdatemanager.createbadgeupdaterforapplication)
- [Native package-family lookup](https://learn.microsoft.com/en-us/windows/win32/api/appmodel/nf-appmodel-getpackagesbypackagefamily)

No literal `C:\BAT` paths were created, modified, deleted, renamed or replaced.
'''

NOTES = r'''# PAFPlayer V512 — visible native lock-screen status

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
'''

def new(path, data):
    with path.open('xb') as stream:
        stream.write(data if isinstance(data, bytes) else data.encode('utf-8'))

def replace(path, text):
    backup(path)
    path.write_text(text, encoding='utf-8')

def main():
    for path in DESTINATIONS:
        if path.exists():
            raise SystemExit('Immutable release destination already exists: ' + str(path))
    source = (ROOT / 'PAFPlayer.py').read_bytes()
    assert b'2026-10-07-v512-lockscreen-visible-status' in source
    import lockscreen_installer as installer
    installer.validate_artifacts(*installer.artifacts(ROOT / 'lockscreen'))
    replace(ROOT / 'docs/windows-lock-screen.md', GUIDE)
    replace(ROOT / 'docs/README.md', '''# PAFPlayer documentation

Current release: **V512**. Native lock-screen status is visible after selecting
**PAFPlayer Lock Screen Recovery** in both slots. UAC remains disabled.

- [V512 release notes](../releases/PAFPlayer_v512_lockscreen_visible_status_release_notes.md)
- [Lock-screen diagnosis, architecture and manual checks](windows-lock-screen.md)
- [V512 manual snapshot](PAFPlayer_v512_lockscreen_visible_status.md)
- [Main manual and historical coverage](../PAFPlayer.md)
- [Visual screensaver (separate feature)](visual-screensaver.md)
- [Playback controls](playback-controls.md)
- [Web configuration](web-config-playback.md)

Reports distinguish user visual confirmation from API-level verification.
No literal C:\\BAT paths changed in this release.
''')
    replace(ROOT / 'lockscreen/README.md', '''# PAFPlayer Lock Screen Recovery — V512

The user confirmed native lock-screen status after selecting **PAFPlayer Lock
Screen Recovery** in both Windows Settings slots. The older music-note entry is
a different identity. UAC remains unchanged at 0. The final V512 update passed
real activation/publication and fixes false offline status after 30 seconds.

See [architecture, diagnosis, limitations and manual checks](../docs/windows-lock-screen.md).
Run `python -B -X utf8 lockscreen_installer.py --check` for a read-only check;
omit `--check` to install, verify actual activation/publication, and run the
publisher. Keep `dist/v512/runtime` in place. Closing hides it to the tray;
use its publishing switch or Exit to disable updates. No login startup is added.

Build with `build_desktop.ps1`, test with `test_desktop.ps1` and
`python -B -X utf8 run_regression_checks.py`. Build output is unique. Make
verified backups before signing both EXE and MSIX, then pin their hashes in the
installer. The existing certificate is public in dist; never distribute its key.

The App.xaml/MainPage.xaml UWP projects and previous build candidates are
historical reference. Current sources are DesktopHost.cs and StatusUpdater.cs.
Do not rerun original-family registration experiments as routine installation.
The original package and prior releases remain preserved.
''')
    manual = ROOT / 'PAFPlayer.md'
    previous = manual.read_text(encoding='utf-8')
    marker = '## Historical comprehensive manual — V448'
    assert marker in previous
    header = '''# PAFPlayer

## Current release — V512

**Source:** `PAFPlayer.py`  
**Snapshot:** `releases/PAFPlayer_v512_lockscreen_visible_status.py`  
**Build ID:** `2026-10-07-v512-lockscreen-visible-status`  
**Updated:** 2026-10-07

Native lock-screen status became visible after selecting **PAFPlayer Lock
Screen Recovery** in both Settings slots. V512 fixes false offline reports
for unchanged player state and keeps that identity. UAC remains disabled.
The final update passed activation/publication; the user visual confirmation
preceded it. Main-player changes are release labels only.

See the [diagnosis and manual checks](docs/windows-lock-screen.md) and
[release notes](releases/PAFPlayer_v512_lockscreen_visible_status_release_notes.md).
The [visual screensaver](docs/visual-screensaver.md) is a separate feature.
`play_audio_file.py` remains untouched. No literal C:\\BAT paths changed.

'''
    replace(manual, header + marker + previous.split(marker, 1)[1])
    new(DESTINATIONS[0], source)
    new(DESTINATIONS[1], NOTES)
    new(DESTINATIONS[2], (ROOT / 'lockscreen/dist/v512/PAFPlayerLockScreen_v512_x64.msix').read_bytes())
    new(DESTINATIONS[5], (ROOT / 'PAFPlayer.md').read_bytes())
    included = [ROOT / 'PAFPlayer.py', ROOT / 'PAFPlayer.md', ROOT / 'docs/windows-lock-screen.md',
                DESTINATIONS[1], DESTINATIONS[5], ROOT / 'lockscreen/dist/PAFPlayerLockScreen_v505.cer']
    included += [ROOT / 'lockscreen' / name for name in (
        'DesktopHost.cs','DesktopHost.manifest','DesktopPackage.appxmanifest','StatusUpdater.cs',
        'StatusUpdaterTests.cs','build_desktop.ps1','test_desktop.ps1','lockscreen_installer.py','README.md')]
    included += sorted((ROOT / 'lockscreen/Assets').glob('PAF*.png'))
    included += sorted(p for p in (ROOT / 'lockscreen/dist/v512').rglob('*') if p.is_file())
    with zipfile.ZipFile(DESTINATIONS[3], 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in included:
            archive.write(path, path.relative_to(ROOT).as_posix())
    manifest = {'version':'V512','packageVersion':'512.0.0.0',
                'visualVerification':'User confirmed Recovery visible before final V512 update; V512 live publication verified.',
                'tests':{'csharp':47,'python':50}, 'literalCBatChanges':[],
                'files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in DESTINATIONS if p != DESTINATIONS[4]}}
    new(DESTINATIONS[4], json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
