"""Package the validated native browser detection fix, preserving replacements."""
import hashlib
import json
from pathlib import Path
from pafplayer_v416_edit import ROOT, replace_file, unique

notes = '''# PAFPlayer V418 — reliable browser playback detection

September 21, 2026. Build `2026-09-21-v418-browser-playback-detection`.

## What failed

The running V417 player reported `Playback monitor disconnected; retrying`, with no active external players. A separate Windows probe reported Chrome as Playing while the user reported YouTube playback. Browser detection is possible on this computer; the player's helper was failing, and its stderr was discarded. The specific cause of that old helper's exit was not recoverable from its status.

## Changes

- Browser/VLC audio detection now runs directly in a background Python thread through Windows Core Audio. Winamp playback state is also queried directly. Neither requires PowerShell, C# compilation, a browser extension, or remote debugging.
- The optional Windows media-session helper now supplies transport state only. It remains useful for silent/muted playback when the browser publishes it. Its failure cannot prevent positive native audio detection.
- Real audio from one tab can override another tab's Paused media-session report. A paused stream with no audio does not override transport state.
- Chrome, Opera/Opera GX, and Edge are recognized, including Edge's packaged application identity. The other previously supported browsers remain recognized.
- A failure on another endpoint no longer vetoes positive playback evidence. Stale evidence is discarded. Missing coverage cannot falsely release an automatic pause after a previously working media-session feed disappears.
- Helper exit codes and diagnostic messages are preserved and shown in the web playback section when fallback is in use. A hung helper is terminated and retried without blocking the native reader or playback thread.
- Existing manual pause/stop ownership and the configurable 15-second automatic-resume fade remain intact.

No browser audio is recorded. The detector reads process names, stream activity, peak levels, and published playback state on the same Windows computer. Browser audio is detected generally; this does not inspect or distinguish YouTube URLs from other sites. Video with neither an audio stream nor a Windows-published playback session cannot be identified by these mechanisms. Remote computers are not monitored.

## Validation

- 42 focused tests pass: 14 new browser/fallback/diagnostic tests, nine previous external-media tests, 13 V417 transport/download tests, one actual player-loop pause/resume integration test, and five embedded media/Winamp regression checks.
- Live native reads detected Chrome's active audio. 100 repeated COM enumerations completed in 1.547 seconds, with all COM references released by the reader.
- The combined live monitor reported Chrome active and generated `external-media-auto-pause` through the real coordinator.
- With helper launch deliberately disabled, native detection still reported Chrome active and healthy, with an explicit fallback diagnostic. No playback-control command was sent to the user's browser during these tests.
- Browser JavaScript syntax checks pass. Opera and Edge identity/decision behavior is covered by tests; they were not separately exercised with live video.
- The full historical 656-test suite was not rerun for this patch. Its previously documented failures remain tracked in the V417 notes.

Live observations: `pafplayer_v418_live_detection.json`. Focused test file: `test_play_audio_file_v418.py`. Restart PAFPlayer to replace the already-running V417 code and start the new native reader.

Windows API references: [audio session enumeration](https://learn.microsoft.com/en-us/windows/win32/api/audiopolicy/nf-audiopolicy-iaudiosessionmanager2-getsessionenumerator), [published media sessions](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession), and [COM threading](https://learn.microsoft.com/en-us/windows/win32/api/objbase/ne-objbase-coinit).
'''
replace_file(ROOT / 'play_audio_file_v418_release_notes.md', notes)
for rel in ('PAFPlayer_changelog.md', 'docs/PAFPlayer_changelog.md'):
    path = ROOT / rel
    prefix = '../' if rel.startswith('docs/') else ''
    entry = f'''## V418 — September 21, 2026

Fixed browser detection's dependency on a failing helper: native Windows audio/Winamp monitoring now works independently, while an optional media-session reader provides silent-playback state. Audible tabs override conflicting paused-tab reports. Added helper diagnostics, stale-feed handling and Edge application-ID recognition; preserved manual pause ownership and the 15-second fade. [Details and live validation]({prefix}play_audio_file_v418_release_notes.md).

'''
    replace_file(path, path.read_text(encoding='utf-8').replace('## V417', entry + '## V417', 1))
path = ROOT / 'docs/play_audio_file.md'
content = path.read_text(encoding='utf-8').replace('Current release: **V417**.', 'Current release: **V418**. See the [V418 browser detection fix](../play_audio_file_v418_release_notes.md).', 1)
needle = '## Automatic pause for other media\n'
content = content.replace(needle, needle + '''
V418 reads browser/VLC audio and Winamp state directly through Windows, independently of the optional media-session helper. Chrome, Opera and Edge are supported. The web playback section reports degraded detection and helper errors. This watches playback on the PAFPlayer computer; silent video requires a Windows-published media session. See [the detection fix and limitations](../play_audio_file_v418_release_notes.md).
''', 1)
replace_file(path, content)
path = ROOT / 'play_audio_file.md'
replace_file(path, path.read_text(encoding='utf-8').replace('[V417 release notes](play_audio_file_v417_release_notes.md)', '[V418 release notes](play_audio_file_v418_release_notes.md)', 1))

source = ROOT / 'play_audio_file.py'
data = source.read_bytes()
compile(data, str(source), 'exec')
snapshot = unique(ROOT / 'play_audio_file_v418_native_browser_detection.py')
snapshot.write_bytes(data)
assert snapshot.read_bytes() == data
installed = Path(r'C:\BAT\play_audio_file.py').read_bytes()
assert hashlib.sha256(installed).hexdigest() == 'ab1f43809af5987e307dd0b9d74a0d8edcc83026f59884fc4ae69b7ed47825b3'
manifest = {'source': str(source), 'versioned_source': str(snapshot),
            'sha256': hashlib.sha256(data).hexdigest(),
            'installed_before_sha256': hashlib.sha256(installed).hexdigest()}
replace_file(ROOT / 'pafplayer_v418_release_manifest.json', json.dumps(manifest, indent=2))
deploy = (ROOT / 'pafplayer_v417_deploy.py').read_text(encoding='utf-8')
replace_file(ROOT / 'pafplayer_v418_deploy.py', deploy.replace('pafplayer_v417_release_manifest', 'pafplayer_v418_release_manifest').replace('pafplayer_v417_deployment', 'pafplayer_v418_deployment'))
print(json.dumps(manifest, indent=2))
