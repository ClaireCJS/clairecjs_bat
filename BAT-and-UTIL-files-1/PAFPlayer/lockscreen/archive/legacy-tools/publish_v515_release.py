"""Preserve V515 source, signed package, documentation and validation evidence."""
from pathlib import Path
import ast
import hashlib
import json
import re
import zipfile
from backup_for_v510 import backup
import lockscreen_installer as installer

ROOT = Path(__file__).resolve().parents[1]
STEM = 'PAFPlayer_v515_managed_lockscreen'

GUIDE = r'''# Windows 10 lock-screen status — V515

PAFPlayer now manages the optional publisher: it starts the installed Windows
app quietly, supplies the local server and current official-instance identity,
restarts failures with a 30-second backoff, and stops it when disabled or when
PAFPlayer exits. The source is included in PAFPlayer.py's application bundle;
there is no additional Python module to copy alongside the player.

**Visible native lock-screen status is still unconfirmed.** V515 fixes automatic
publisher ownership and startup. It does not claim to have established the cause
of every earlier blank-screen report. Successful publication, Settings selection,
Appx status Ok and background registration are not visual proof.

## Enable and use

Install the signed companion once, under the Windows account that plays music:

```powershell
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py --check
& C:\ProgramData\anaconda3\python.exe -B -X utf8 lockscreen\lockscreen_installer.py
```

The installer validates the package and executable hashes, certificate signer,
manifest, real interactive activation, publication receipt and background COM
activation. `--check` is read-only. The executable and assets are included in a
self-contained MSIX; there is no external runtime directory. The current package
version is `515.0.0.1`, and its display name is **PAFPlayer Lock Screen V515**.

In PAFPlayer's web configuration, **Windows Lock Screen → Enable lock-screen song
status** controls publishing. Fresh installations default to off. An explicit
saved companion preference is migrated, with a saved PAFPlayer choice taking
precedence. Once enabled, no companion window needs to be opened manually.
The currently playing V514 process has not been restarted: automatic management
takes effect when V515 is next launched. An independent publisher was restored
for that existing playback session after the live tests.

In Windows Settings → Personalization → Lock screen, choose the versioned app:

- **Choose one app to show detailed status:** song, artist/playback state, lyric.
- **Choose which apps show quick status:** playing, paused, idle or offline badge.

Both may be selected. They serve different purposes. Windows owns the picker;
PAFPlayer cannot silently choose a status slot. The original unversioned app is
a different identity. The Recovery family and `!App` ID remain unchanged from
V511–V514, preserving selection and registration compatibility.

## Architecture and playback isolation

`lockscreen/src/PAFPlayer_lockscreen.py` is bundled into the single-file player.
One daemon controller starts after the web server binds. It checks official
instance ownership and saved settings every five seconds; all package discovery,
signature verification and activation happen on that worker, never in an audio
callback or visualizer frame. Web-server shutdown signals it without waiting for
Windows. Optional startup failures are contained and shown in the setting status.

Windows must own a registered app identity for the selected tile and badge. The
player uses IApplicationActivationManager to start that identity with managed
arguments. A direct CreateProcess attempt against WindowsApps failed with
ERROR_ACCESS_DENIED on this computer; the supported activation API passed.
See Microsoft's [packaged application activation API](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-iapplicationactivationmanager-activateapplication)
and [package identity guidance](https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/grant-identity-to-nonpackaged-apps).

The separate .NET publisher owns the Windows notification APIs. It is headless
in managed mode, checks a uniquely named owner stop event and the launching
process, and clears its own tile/badge on normal stop. This also covers owner
exit after a crash. Existing notifications expire after 90 seconds if cleanup
cannot run. PAFPlayer sends no audio commands to manage this process.

The helper verifies `/api/remote-tray/hello` using GET only: `official=true`,
case-insensitive PAFPlayer names in root/state, matching nonempty versions and a
nonempty identity. Managed mode additionally pins that identity to the launching
official instance and accepts only a loopback address. It refuses another player
session. Network failure removes stale track data and publishes offline status.
Redirects, proxies, cookies and default credentials are disabled; responses and
timeouts are bounded. The helper never calls playback-command endpoints.

The five-second refresh does not activate the browser spectrum or decode artwork.
The new settings endpoint is loopback-only; mutations require the existing
workflow token and same-origin checks. Existing configuration IDs are unchanged.
`PAFPlayerLockScreenEnabled` is retained in player workflow settings and companion
JSON; `PAFPlayerServerUrl` is retained. `PAFPlayerManagedPublisher` is new private
companion metadata. The Windows background registration remains, but its timer
does not publish independently for a managed session after its owner has stopped.

## Diagnosis and Windows limitations

The original identity failed activation with `0x80270254`
(`E_APPLICATION_NOT_REGISTERED`) despite Appx status Ok. The Recovery identity
activates with UAC disabled. This is evidence against treating UAC as the sole
cause, but it does not prove native lock-screen rendering works.

At the start of this change the official V514 server was running while no
publisher process was present. Ninety-second notification expiry makes that a
real availability gap. V515 supplies automatic startup/restart and lifecycle
ownership. During later checks the independently running V515 helper persisted
and Windows recorded tile/badge deliveries every five seconds.

The earlier blank display while publication was active remains unexplained.
No supported evidence has established that UAC must be changed or that native
status is impossible with it disabled. UAC, Windows notification/privacy policies,
private notification databases and Windows registration caches were not modified.
A four-minute read-only process sampler recorded the publisher, but no new
user-confirmed lock cycle was returned, so it cannot establish renderer behavior.

Microsoft documents the [lock-screen background-task requirement](https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-uap-lockscreen)
and [Windows 10 COM task registration](https://learn.microsoft.com/en-us/uwp/api/windows.applicationmodel.background.backgroundtaskbuilder.settaskentrypointclsid).
Registration/access and COM interface activation passed. Actual scheduled timer
execution remains separately unverified. Windows controls refresh, layout and
truncation; this feature is not a .scr screensaver, wallpaper overlay, SMTC media
panel or arbitrary drawing on the secure desktop. Native status cannot reproduce
the artwork-rich screensaver.

## Verification

- **120 focused tests passed:** 51 C# payload/network/identity tests and 69 Python
  installer, tray, lifecycle and real HTTP settings tests.
- **678 embedded tests ran on both V515 and the immutable V514 baseline.** Each
  produced 614 passes, 51 failures and 13 errors, with identical failing test
  names. There were no newly failing tests in that comparison. This is not a clean
  full-suite pass: obsolete historical assertions and guarded database tests
  still need separate maintenance. Reports retain the actual failures.
- C# compilation, full MakeAppx validation, EXE/MSIX signatures and pinned package
  checks passed. The old obsolete-enum compatibility warning remains.
- Real V515 activation/publication ran under DEMONA\Claire in console session 1
  with `EnableLUA=0`. Headless managed launch, graceful stop and rejection of a
  wrong official identity passed twice. The receipt contained real song/lyric
  text and a playing badge. Neither receipt is proof of visible rendering.
- The source bundle matches its module. Previous releases were not overwritten;
  replacements used verified backups. `play_audio_file.py` was not modified.

Reports are directly in `tests/reports`, including the V515 focused regressions,
managed live checks, C# tests and V514 baseline comparison. Run
`lockscreen/run_regression_checks.py`, `lockscreen/test_desktop.ps1`, and
`lockscreen/run_embedded_v515.py` for isolated checks. Run
`lockscreen/verify_managed_live.py` only in the interactive account; it briefly
replaces this companion for lifecycle testing and restores independent publishing.
It does not control or restart audio.

Manual verification: launch V515, confirm the Windows Lock Screen checkbox and
publisher status, select V515 in both Windows slots, then lock Windows yourself.
Check the clock-and-date wallpaper before dismissing it for password/PIN entry.
Check song changes, timed lyrics and playing/paused badges using normal player
controls. Disable the setting to check clearing, reenable to check automatic
restart, and close PAFPlayer to check helper exit. The agent does not operate or
capture the secure desktop. **Visible text/badges are the remaining acceptance
check; a blank screen keeps the rendering issue open.**

No literal `C:\BAT` paths were created, modified or deleted.
'''

NOTES = r'''# PAFPlayer V515 — managed lock-screen publisher

PAFPlayer now starts, configures, restarts and stops its optional signed Windows
publisher automatically. A web-setting checkbox uses the preserved
PAFPlayerLockScreenEnabled key. Existing explicit companion preferences migrate;
fresh installs remain disabled. The helper is headless, pins the official local
player identity, and sends no playback commands. All activation work runs outside
the audio/render loops. Windows app activation replaces a direct executable
launch that failed with access denied on this machine.

**This release does not claim the remaining blank native lock screen is fixed.**
Automatic lifecycle, installed-package activation and publication passed actual
interactive checks. Native visible rendering still awaits the user's check.
UAC remains unchanged and disabled. The currently playing V514 process was not
restarted; automatic management starts with the next V515 player launch.

120 focused tests passed. The full 678 embedded tests ran on V515 and unchanged
V514: both had the same 51 failures and 13 errors (614 passes). No new failing
test names appeared; these results are not a clean full-suite pass. Compilation,
full package validation, signatures, interactive activation/publication, headless
launch, session pinning and graceful shutdown passed. Scheduled timer execution
and locked-screen appearance remain unverified.

The installed package is 515.0.0.1, displayed as PAFPlayer Lock Screen V515.
Family/App ID and earlier configuration IDs are preserved. Earlier releases and
build candidates remain intact. play_audio_file.py was not changed.

No literal C:\BAT paths were created, modified or deleted.

See the [architecture, limitations and manual verification](../docs/windows-lock-screen.md).
'''


def write_new(path, value):
    with path.open('xb') as stream:
        stream.write(value if isinstance(value, bytes) else value.encode('utf-8'))


def replace(path, value):
    backup(path)
    path.write_text(value, encoding='utf-8')


def main():
    outputs = [ROOT / 'releases' / (STEM + '.py'),
               ROOT / 'releases' / (STEM + '_release_notes.md'),
               ROOT / 'releases/PAFPlayer_v515_lockscreen_x64.msix',
               ROOT / 'releases/PAFPlayer_v515_lockscreen_release_bundle.zip',
               ROOT / 'docs' / (STEM + '.md'),
               ROOT / 'releases' / (STEM + '_manifest.json')]
    if any(p.exists() for p in outputs):
        raise RuntimeError('Release output already exists; never overwrite it.')
    package, certificate, deps = installer.artifacts(ROOT / 'lockscreen')
    installer.validate_artifacts(package, certificate, deps)
    source = (ROOT / 'PAFPlayer.py').read_bytes()
    ast.parse(source)
    assert b'2026-10-08-v515-managed-lockscreen' in source
    replace(ROOT / 'docs/windows-lock-screen.md', GUIDE)
    replace(ROOT / 'lockscreen/README.md', '''# PAFPlayer Lock Screen V515

PAFPlayer manages the installed publisher automatically. Native visible rendering
remains unconfirmed; publication is not visual proof.

See the [architecture, controls and manual verification](../docs/windows-lock-screen.md).
The current full MSIX is in dist/v515; install with lockscreen_installer.py.
Run run_regression_checks.py and test_desktop.ps1 for focused tests.
run_embedded_v515.py runs all embedded player tests with isolated write guards.
build_desktop.ps1 accepts -SigningThumbprint and preserves signing backups.
Do not overwrite release artifacts or distribute private signing keys.
''')
    replace(ROOT / 'docs/README.md', '''# PAFPlayer documentation

Current release: **V515** — automatic lock-screen publisher management.
Native visible status remains unconfirmed.

- [V515 release notes](../releases/PAFPlayer_v515_managed_lockscreen_release_notes.md)
- [Lock-screen architecture and verification](windows-lock-screen.md)
- [V515 manual snapshot](PAFPlayer_v515_managed_lockscreen.md)
- [Main manual and historical coverage](../PAFPlayer.md)
- [Separate visual screensaver](visual-screensaver.md)
- [Playback controls](playback-controls.md)
- [Web configuration](web-config-playback.md)
''')
    manual = ROOT / 'PAFPlayer.md'
    previous = manual.read_text(encoding='utf-8')
    marker = '## Historical comprehensive manual — V448'
    assert marker in previous
    header = '''# PAFPlayer

## Current release — V515

**Source:** `PAFPlayer.py`  
**Snapshot:** `releases/PAFPlayer_v515_managed_lockscreen.py`  
**Build ID:** `2026-10-08-v515-managed-lockscreen`  
**Updated:** 2026-10-08

PAFPlayer now manages its optional Windows lock-screen publisher automatically,
with a web-setting checkbox, official-instance identity pinning, bounded restart
and cooperative shutdown. The publisher remains a separate process and is
headless when managed by PAFPlayer. Windows requires its registered app identity.

Native visible status remains unconfirmed. 120 focused tests pass; a comparison
of all 678 embedded tests found the same 64 nonpassing tests on V514 and V515.
Actual managed launch, shutdown, activation and publication were checked with
UAC disabled. This does not substitute for a locked-screen visual check.

See the [architecture and manual verification](docs/windows-lock-screen.md) and
[release notes](releases/PAFPlayer_v515_managed_lockscreen_release_notes.md).
The [visual screensaver](docs/visual-screensaver.md) remains separate.
UAC and play_audio_file.py were not changed. No literal C:\\BAT paths changed.

'''
    replace(manual, header + marker + previous.split(marker, 1)[1])
    write_new(outputs[0], source)
    write_new(outputs[1], NOTES)
    write_new(outputs[2], package.read_bytes())
    snapshot = re.sub(r'\]\((?!https?:|#|/)([^)]+)\)', r'](../\1)', manual.read_text(encoding='utf-8'))
    write_new(outputs[4], snapshot)
    included = [ROOT / 'PAFPlayer.py', manual, ROOT / 'docs/windows-lock-screen.md',
                outputs[1], outputs[4], package, certificate]
    included += [ROOT / 'lockscreen' / name for name in (
        'PAFPlayer_lockscreen.py', 'DesktopHost.cs', 'DesktopBackground.cs', 'ManagedPublisher.cs',
        'DesktopHost.manifest', 'DesktopPackage.appxmanifest', 'StatusUpdater.cs', 'StatusUpdaterTests.cs',
        'build_desktop.ps1', 'test_desktop.ps1', 'lockscreen_installer.py', 'test_managed_publisher.py',
        'run_regression_checks.py', 'run_embedded_v515.py', 'verify_managed_live.py', 'README.md')]
    included += sorted((ROOT / 'lockscreen/Assets').glob('PAF*.png'))
    with zipfile.ZipFile(outputs[3], 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in included:
            archive.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(outputs[3]) as archive:
        assert archive.testzip() is None
        assert not any(name.lower().endswith('.pfx') for name in archive.namelist())
    manifest = {'version': 'V515', 'packageVersion': installer.PACKAGE_VERSION,
                'displayName': installer.PACKAGE_DISPLAY_NAME, 'rendering': 'unconfirmed; issue remains open',
                'focusedTests': {'csharpPassed': 51, 'pythonPassed': 69},
                'embeddedComparison': {'each': 678, 'passed': 614, 'failures': 51, 'errors': 13, 'newFailingNames': []},
                'literalCBatChanges': [],
                'files': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs[:-1]}}
    write_new(outputs[-1], json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
