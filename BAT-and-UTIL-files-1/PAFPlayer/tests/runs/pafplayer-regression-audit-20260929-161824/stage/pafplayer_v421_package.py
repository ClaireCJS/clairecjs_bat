import hashlib
import json
from pathlib import Path
from pafplayer_v416_edit import ROOT, replace_file, unique

notes = '''# PAFPlayer V421 — manual Play wins

September 21, 2026. Build `2026-09-21-v421-manual-play-override`.

V420 gave detected external playback unconditional priority and refused manual Play. This was incorrect: it trapped the user in an automatic hold whenever background media remained active.

V421 treats the first observed media state as the background baseline. Those already-active applications do not interrupt startup. A newly active application pauses PAFPlayer. Play (including the Winamp-compatible URL) or Space while paused resumes immediately and acknowledges currently active applications, preventing an immediate repeat pause. Acknowledgements are per application; an acknowledged Chrome video cannot hide a newly started VLC player. Each application's acknowledgement expires after that application is confirmed inactive for 1.5 seconds, independently of the other applications. Unknown monitor data neither expires an acknowledgement nor blocks manual Play.

Automatic holds resume after the interrupting applications finish and the quiet interval passes, even if acknowledged background media continues. The automatic fade remains 15 seconds by default and configurable in web playback settings. Manual Play is immediate. Manual Pause and Stop still cancel automatic resumption. Web help now explains Play correctly, and status exposes `external_media_acknowledged` for diagnosis.

Detection currently groups sources by application: it does not distinguish a second Chrome tab while another Chrome tab is acknowledged. A browser must become inactive before that browser can interrupt again. This is not a per-tab timestamp or media identity implementation.

Validation: 51 focused tests passed across V421, updated V420 control/player-loop tests, V416 external media, V418 detectors, and V417 transport/downloads. Existing tests now establish an idle baseline before simulating newly started media; assertions requiring Play to remain blocked were replaced with the corrected behavior. The full-loop test verifies manual Play, a subsequent VLC interruption while Chrome continues, automatic fade, and manual hold.

A separate muted real-player test used live native detection of Chrome and VLC, an explicitly injected idle baseline, and real IsolatedWaveOutProcess workers. It verified worker shutdown on automatic pause, restart after Play, and continued playback with both external applications still active. Report: `pafplayer_v421_live_player_check.json`. Test-harness timing/post-Stop assertions were corrected before the passing run; no user's media app was controlled. The historical full suite was not rerun.

Preserves the earlier timing, karaoke, emoji, downloads and transport changes. Restart PAFPlayer and confirm V421 to load this correction; an already-running V420 process is unchanged.
'''
replace_file(ROOT/'play_audio_file_v421_release_notes.md', notes)
for rel in ('PAFPlayer_changelog.md', 'docs/PAFPlayer_changelog.md'):
    path = ROOT/rel
    prefix = '../' if rel.startswith('docs/') else ''
    entry = f'''## V421 — September 21, 2026

Restored immediate manual Play/Space after automatic pause. Already-playing background applications are ignored at startup; overrides apply only to current applications and expire independently after inactivity, so newly started VLC can still interrupt an overridden Chrome video. Retains automatic 15-second fade and manual Pause/Stop ownership. 51 focused tests and real-worker manual-resume validation passed. [Details and detection limits]({prefix}play_audio_file_v421_release_notes.md).

'''
    replace_file(path, path.read_text(encoding='utf-8').replace('# PAFPlayer changelog\n', '# PAFPlayer changelog\n\n'+entry, 1))
path=ROOT/'docs/play_audio_file.md'
s=path.read_text(encoding='utf-8').replace('Current release: **V420**. See the [V420 pause-priority repair](../play_audio_file_v420_release_notes.md).', 'Current release: **V421**. See the [V421 manual Play correction](../play_audio_file_v421_release_notes.md).')
s=s.replace('Manual Pause stays paused. Play while other media is active waits for that media to finish; disable automatic pause to play both simultaneously.', 'Manual Pause stays paused. Play resumes immediately and overrides currently active applications until each becomes inactive. Existing background media is ignored at startup; newly active applications can still interrupt. Detection groups browser tabs by application.')
replace_file(path,s)
path=ROOT/'play_audio_file.md'
replace_file(path,path.read_text(encoding='utf-8').replace('[V420 release notes](play_audio_file_v420_release_notes.md)', '[V421 release notes](play_audio_file_v421_release_notes.md)',1))
source=ROOT/'play_audio_file.py'
data=source.read_bytes()
compile(data,str(source),'exec')
snapshot=unique(ROOT/'play_audio_file_v421_manual_play_override.py')
snapshot.write_bytes(data)
assert snapshot.read_bytes()==data
manifest={'source':str(source),'versioned_source':str(snapshot),'sha256':hashlib.sha256(data).hexdigest(), 'installed_before_sha256':hashlib.sha256(Path(r'C:\BAT\play_audio_file.py').read_bytes()).hexdigest()}
replace_file(ROOT/'pafplayer_v421_release_manifest.json',json.dumps(manifest,indent=2))
deploy=(ROOT/'pafplayer_v420_deploy.py').read_text(encoding='utf-8').replace('pafplayer_v420_release_manifest','pafplayer_v421_release_manifest').replace('pafplayer_v420_deployment','pafplayer_v421_deployment')
replace_file(ROOT/'pafplayer_v421_deploy.py',deploy)
print(json.dumps(manifest,indent=2))
