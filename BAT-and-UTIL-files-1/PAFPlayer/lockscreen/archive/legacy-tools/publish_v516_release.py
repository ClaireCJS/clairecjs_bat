"""Release the reproduced oversized-environment launcher fix; keep V515 intact."""
from pathlib import Path
import ast
import hashlib
import json
import re
import zipfile
from backup_for_v510 import backup
import lockscreen_installer as installer

ROOT = Path(__file__).resolve().parents[1]
STEM = 'PAFPlayer_v516_lockscreen_launch_environment'
NOTES = r'''# PAFPlayer V516 — fix lock-screen launch from the music shell

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
'''


def new(path, value):
    with path.open('xb') as stream:
        stream.write(value if isinstance(value, bytes) else value.encode('utf-8'))


def replace(path, value):
    backup(path)
    path.write_text(value, encoding='utf-8')


def main():
    outputs = [ROOT / 'releases' / (STEM + '.py'), ROOT / 'releases' / (STEM + '_release_notes.md'),
               ROOT / 'releases/PAFPlayer_v516_lockscreen_x64.msix',
               ROOT / 'releases/PAFPlayer_v516_lockscreen_release_bundle.zip',
               ROOT / 'docs' / (STEM + '.md'), ROOT / 'releases' / (STEM + '_manifest.json')]
    assert not any(path.exists() for path in outputs), 'Never overwrite release artifacts'
    package, certificate, dependencies = installer.artifacts(ROOT / 'lockscreen')
    installer.validate_artifacts(package, certificate, dependencies)
    source = (ROOT / 'PAFPlayer.py').read_bytes()
    assert b'2026-10-08-v516-lockscreen-launch-environment' in source
    old = ast.parse((ROOT / 'releases/PAFPlayer_v515_managed_lockscreen.py').read_bytes())
    current = ast.parse(source)
    def definitions(tree):
        return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert definitions(old) == definitions(current), 'Unexpected main-player code change'
    guide = (ROOT / 'docs/windows-lock-screen.md').read_text(encoding='utf-8')
    guide = guide.replace('# Windows 10 lock-screen status — V515', '# Windows 10 lock-screen status — V516')
    guide = guide.replace('PAFPlayer Lock Screen V515', 'PAFPlayer Lock Screen V516').replace('`515.0.0.1`', '`516.0.0.0`')
    guide = guide.replace('**Visible native lock-screen status is still unconfirmed.** V515 fixes automatic\npublisher ownership and startup.',
                          '**Visible native lock-screen status is still unconfirmed.** V516 fixes the\nreproduced oversized-environment failure in V515 automatic startup.')
    guide = guide.replace('The currently playing V514 process has not been restarted: automatic management\ntakes effect when V515 is next launched.',
                          'The running player was verified as V515 and was not restarted. The corrected\nlauncher is loaded when V516 is next launched.')
    guide = guide.replace('V511–V514, preserving', 'V511–V515, preserving')
    diagnosis = '''## V516 launch failure and fix

The live V515 server reported publishing enabled but the launcher returned an
incorrect install-package message. Its installed signed package was valid.
Reproducing the child launch using the actual player's environment exposed
PowerShell Add-Type's compiler error: the environment block was 142043 bytes,
larger than its reported 65535-byte maximum. This explains why launching from
the separate diagnostic shell succeeded while automatic player startup failed.

Only the activation child now receives an allowlist of Windows/profile/temp
variables plus Windows tool paths. Its environment is approximately 1 KB.
The player's own environment and custom shell configuration remain unchanged.
The installer uses the same isolation. Windows failure text is captured as UTF-8
and surfaced in the setting status instead of an unconditional reinstall message.
The corrected launcher was tested with that same live player's environment and
working directory: headless activation, official-player publication and graceful
shutdown passed. The original failure and corrected results are retained in
tests/reports/v515-player-environment-* and v516-player-environment-*.

'''
    guide = guide.replace('## Architecture and playback isolation\n', diagnosis + '## Architecture and playback isolation\n')
    guide = guide.replace('**120 focused tests passed:** 51 C# payload/network/identity tests and 69 Python',
                          '**123 focused tests passed:** 51 C# payload/network/identity tests and 72 Python')
    guide = guide.replace('**678 embedded tests ran on both V515 and the immutable V514 baseline.**',
                          '**Prior comparison: 678 embedded tests ran on V515 and the immutable V514 baseline.**')
    guide = guide.replace('  still need separate maintenance. Reports retain the actual failures.',
                          '  still need separate maintenance. Reports retain the actual failures. These\n  678 tests were not rerun for V516: its main-player function/class bodies match\n  V515 exactly; the change is confined to the bundled launcher and release constants.')
    guide = guide.replace('Manual verification: launch V515,', 'Manual verification: launch V516,')
    guide = guide.replace('select V515 in both Windows slots', 'select V516 in both Windows slots')
    guide = guide.replace('`lockscreen/verify_managed_live.py` only in the interactive account;',
                          '`lockscreen/verify_player_environment_v516.py <player-pid>` only in the interactive account;')
    replace(ROOT / 'docs/windows-lock-screen.md', guide)
    replace(ROOT / 'lockscreen/README.md', '''# PAFPlayer Lock Screen V516

Fixes automatic launch from large music-shell environments without changing the
player's environment. Native visible rendering remains unconfirmed.

See the [architecture, controls and verification](../docs/windows-lock-screen.md).
Install the signed package in dist/v516 with lockscreen_installer.py.
Run run_regression_checks.py and test_desktop.ps1 for focused checks.
build_desktop.ps1 signs only with verified signing backups; releases are immutable.
''')
    index = (ROOT / 'docs/README.md').read_text(encoding='utf-8').replace('V515', 'V516').replace('v515_managed_lockscreen', 'v516_lockscreen_launch_environment')
    index = index.replace('automatic lock-screen publisher management', 'lock-screen launch environment fix')
    replace(ROOT / 'docs/README.md', index)
    manual = ROOT / 'PAFPlayer.md'
    previous = manual.read_text(encoding='utf-8')
    marker = '## Historical comprehensive manual — V448'
    assert marker in previous
    header = '''# PAFPlayer

## Current release — V516

**Source:** `PAFPlayer.py`  
**Snapshot:** `releases/PAFPlayer_v516_lockscreen_launch_environment.py`  
**Build ID:** `2026-10-08-v516-lockscreen-launch-environment`  
**Updated:** 2026-10-08

Fixes the V515 publisher launch failure caused by the actual player's oversized
inherited shell environment. Only the Windows activation child gets a small
environment; the player's environment and playback are untouched. Actual launch
errors now appear in the setting status. The installed picker name is
PAFPlayer Lock Screen V516, with the same app identity and settings keys.

123 focused tests passed, along with real activation/publication and shutdown
using the live player's environment. Native locked-screen appearance remains
unverified; a successful notification API call is not visual proof.

See the [architecture and manual verification](docs/windows-lock-screen.md) and
[release notes](releases/PAFPlayer_v516_lockscreen_launch_environment_release_notes.md).
The [visual screensaver](docs/visual-screensaver.md) remains separate.
UAC and play_audio_file.py were not changed. No literal C:\\BAT paths changed.

'''
    replace(manual, header + marker + previous.split(marker, 1)[1])
    new(outputs[0], source)
    new(outputs[1], NOTES)
    new(outputs[2], package.read_bytes())
    new(outputs[4], re.sub(r'\]\((?!https?:|#|/)([^)]+)\)', r'](../\1)', manual.read_text(encoding='utf-8')))
    included = [ROOT / 'PAFPlayer.py', manual, ROOT / 'docs/windows-lock-screen.md', outputs[1], outputs[4], package, certificate]
    included += [ROOT / 'lockscreen' / name for name in (
        'PAFPlayer_lockscreen.py', 'DesktopHost.cs', 'DesktopBackground.cs', 'ManagedPublisher.cs',
        'DesktopHost.manifest', 'DesktopPackage.appxmanifest', 'StatusUpdater.cs', 'StatusUpdaterTests.cs',
        'build_desktop.ps1', 'test_desktop.ps1', 'lockscreen_installer.py', 'test_managed_publisher.py',
        'run_regression_checks.py', 'verify_player_environment_v516.py', 'README.md')]
    included += sorted((ROOT / 'lockscreen/Assets').glob('PAF*.png'))
    with zipfile.ZipFile(outputs[3], 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in included: archive.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(outputs[3]) as archive:
        assert archive.testzip() is None
        assert archive.read('PAFPlayer.py') == source
        assert not any(n.lower().endswith('.pfx') for n in archive.namelist())
    manifest = {'version': 'V516', 'packageVersion': installer.PACKAGE_VERSION,
                'displayName': installer.PACKAGE_DISPLAY_NAME,
                'rootCause': 'PowerShell Add-Type rejected the running player inherited environment block (142043 bytes)',
                'launchFix': 'verified with actual player environment', 'rendering': 'unconfirmed',
                'focusedTests': {'csharpPassed': 51, 'pythonPassed': 72},
                'mainPlayerFunctionClassChangesFromV515': [], 'literalCBatChanges': [],
                'files': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs[:-1]}}
    new(outputs[-1], json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
