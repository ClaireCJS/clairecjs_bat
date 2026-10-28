"""Package external-media priority repair without losing the user's V419 work."""
import hashlib
import json
from pathlib import Path
from pafplayer_v416_edit import ROOT, replace_file, unique

notes = '''# PAFPlayer V420 — external-media priority after Play/resume

September 21, 2026. Build `2026-09-21-v420-external-media-priority`.

## Failure and repair

The running V419 status showed Chrome active, detection healthy, automatic pause enabled, and PAFPlayer still playing. Trace history contained pause/resume actions. The coordinator's `override_until_quiet` latch explained that combination: Play/resume bypassed automatic pause until every external player was confirmed quiet for 1.5 seconds. A continuing browser session could leave that bypass active across songs and even suppress a newly started VLC player. Play during monitor startup could also arm the bypass before any positive detection.

V420 removes that bypass. While **Pause for VLC, Winamp and browser media** is enabled, detected external playback retains priority. Pressing Play while other media is active keeps PAFPlayer automatically held and requests resumption after that media finishes. Turn the setting off to permit simultaneous playback.

Manual Pause and Stop still remain held after external media finishes. Automatic holds still resume after 1.5 seconds of confirmed quiet, with the configured fade (15 seconds by default). The web explanation reflects this behavior. Status now includes `external_media_decision`, and diagnostic traces distinguish `external-media.pause` / `external-media.resume` from ordinary pause toggles.

This release preserves the V419 album-art emoji-spacing change already present in the workspace, as well as the V418 native detector and V417 Winamp-compatible URLs/downloads.

## Validation

- 43 focused tests pass: seven new priority/player-loop regressions, nine external-media tests, 14 detection/fallback tests, and 13 web transport/download tests. The old test that required Play to bypass priority was updated to the corrected behavior.
- Full-loop regression exercises Chrome detection, Play and Space attempts during the automatic hold, VLC joining, both sources finishing, a 15-second fade, another VLC interruption, and a manual hold that must not auto-resume.
- Live Chrome test: real Windows detection caused the actual PAFPlayer loop to stop an `IsolatedWaveOutProcess` (running before the pause, exited afterward). Play remained held. Test audio volume was zero; the user's existing player/browser was not controlled.
- Live VLC test: a separate hidden VLC instance played a silent WAV. The real PAFPlayer loop stopped its real audio worker and kept Play held. Chrome was filtered out only inside the test to establish that VLC independently caused the result. Only the test VLC instance was closed afterward. Earlier isolated VLC launches did not expose a stream until first-run prompts were explicitly disabled in the test launch.
- Reports: `pafplayer_v420_live_player_check.json` (Chrome), `pafplayer_v420_live_player_check (1).json` (VLC).

The live checks verify actual playback-worker shutdown, not only detector output. They do not hot-patch the already-running V419 user session: restart PAFPlayer and confirm V420 in its web status/version badge. The historical full suite was not rerun for this focused repair.
'''
replace_file(ROOT / 'play_audio_file_v420_release_notes.md', notes)
for rel in ('PAFPlayer_changelog.md', 'docs/PAFPlayer_changelog.md'):
    path = ROOT / rel
    prefix = '../' if rel.startswith('docs/') else ''
    entry = f'''## V420 — September 21, 2026

Removed the Play/resume bypass that could disable external-media priority indefinitely while a browser stayed active. Enabled automatic pause now keeps competing media in priority; manual Pause/Stop ownership and the configured fade remain. Added decision diagnostics and verified actual audio-worker shutdown with live Chrome and VLC. Preserves V419's album-art spacing repair. [Validation and behavior]({prefix}play_audio_file_v420_release_notes.md).

'''
    content = path.read_text(encoding='utf-8')
    replace_file(path, content.replace('# PAFPlayer changelog\n', '# PAFPlayer changelog\n\n' + entry, 1))
path = ROOT / 'docs/play_audio_file.md'
content = path.read_text(encoding='utf-8').replace('Current release: **V418**.', 'Current release: **V420**. See the [V420 pause-priority repair](../play_audio_file_v420_release_notes.md).', 1)
content = content.replace('Manual Pause stays paused; explicit Play overrides the current interruption.', 'Manual Pause stays paused. Play while other media is active waits for that media to finish; disable automatic pause to play both simultaneously.')
replace_file(path, content)
path = ROOT / 'play_audio_file.md'
replace_file(path, path.read_text(encoding='utf-8').replace('[V418 release notes](play_audio_file_v418_release_notes.md)', '[V420 release notes](play_audio_file_v420_release_notes.md)', 1))
source = ROOT / 'play_audio_file.py'
data = source.read_bytes()
compile(data, str(source), 'exec')
snapshot = unique(ROOT / 'play_audio_file_v420_external_media_priority.py')
snapshot.write_bytes(data)
assert snapshot.read_bytes() == data
installed = Path(r'C:\BAT\play_audio_file.py').read_bytes()
manifest = {'source': str(source), 'versioned_source': str(snapshot),
            'sha256': hashlib.sha256(data).hexdigest(),
            'installed_before_sha256': hashlib.sha256(installed).hexdigest()}
replace_file(ROOT / 'pafplayer_v420_release_manifest.json', json.dumps(manifest, indent=2))
deploy = (ROOT / 'pafplayer_v418_deploy.py').read_text(encoding='utf-8')
replace_file(ROOT / 'pafplayer_v420_deploy.py', deploy.replace('pafplayer_v418_release_manifest', 'pafplayer_v420_release_manifest').replace('pafplayer_v418_deployment', 'pafplayer_v420_deployment'))
print(json.dumps(manifest, indent=2))
