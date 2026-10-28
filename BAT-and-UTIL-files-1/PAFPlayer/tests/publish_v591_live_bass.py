"""Document and publish immutable V591 artifacts after focused verification."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'monkeymote/research'))
from edit_v568 import write

source=root/'PAFPlayer.py'
sha=hashlib.sha256(source.read_bytes()).hexdigest()
checks=json.loads((root/'tests/reports/v591-bass-checks-20261021-104104.json').read_text())
assert checks['tests']==70 and checks['failures']==1 and checks['errors']==0
assert next(c['sha256'] for c in checks['copies'] if c['source']==str(source))==sha
native=json.loads((root/'tests/reports/v591-native-muted-20261021-104335.json').read_text())
assert native['source_sha256']==sha and native['volume']==0 and len(native['changes'])==2
assert max(s['health']['underruns'] for s in native['samples'])==0
name='PAFPlayer_v591_live_bass_transitions'
for suffix in ('.py','.md','_release_notes.md'):
    assert not (root/'releases'/(name+suffix)).exists(), 'Release already exists; do not overwrite'

section='''## V591 live bass transitions

The buffered WaveOut renderer now changes its running FFmpeg bass filter when
Windows locks or unlocks. It keeps the decoder, audio worker, queued PCM, output
device and playback clock running. Web Playback bass controls use the same live
path, including enabling or disabling bass boost. This removes the deliberate
stop/relaunch gap introduced by changing the filter in earlier versions.

The existing 120 Hz low shelf, percentage mapping, filter order before speaker
expansion, setting IDs and CLI overrides are preserved. Each selected output
receives the change. The named filter remains available at 0 dB so unlocking can
restore normal bass without rebuilding the stream. Commands use a private pipe,
not the user's console, and no extra DSP dependency is required.

Windows lock detection still runs once per second. Existing decoder/output
queues must drain before a change becomes audible; V591 does not promise an
instant change at the exact lock event. Legacy FFplay still needs the existing
same-position restart and can have a gap. Use the buffered renderer for this fix.
The running V590 process must be restarted to load V591.

Verification: 69 of 70 focused and relevant existing tests passed. The remaining
`test_seek_restarts_ffplay_at_requested_offsets` failure (expected three commands,
got two) is already recorded against V589 and V590; it is not introduced here.
An actual FFmpeg 4.2.3 stream at 96 kHz / 8 channels / 24-bit delivered all 672,000
frames while switching 0 → -14 → 0 dB. Every 10 ms block retained audio and the
final marker survived. A real Windows WaveOut worker, muted for testing, retained
one PID through both changes, reached six seconds and reported zero underruns.
No listening test of V591 has been performed yet.

Manual verification:

1. Restart the normal player with V591 and the buffered renderer enabled. Keep
   the existing bass-reduction checkbox and desired reduction amount selected.
2. Play a track with sustained bass, lock Windows for about 15 seconds, then
   unlock. Bass should reduce and restore without an intervening silence or a
   song-position jump. Allow the one-second polling and existing queued audio.
3. Adjust the bass controls in Web Playback while playing; confirm the same
   uninterrupted behavior. If using several output devices, check each one.
4. Repeat across pause/resume and a natural song ending. Paused/queued audio can
   delay the audible filter update; the ending should still play completely.

FFmpeg documents runtime bass-gain commands in its
[bass filter documentation](https://ffmpeg.org/ffmpeg-filters.html#bass_002c-lowshelf).
The private Windows stdin command path was also verified against the installed
binary, with successful command replies and measured decoded audio.

'''
path='docs/playback-controls.md'
write(path,section+(root/path).read_text(encoding='utf-8'))
path='docs/README.md'
s=(root/path).read_text(encoding='utf-8')
s=s.replace('Current release: **V590** — reliable locked-session bass reduction and same-song filter restarts.',
            'Current release: **V591** — live bass changes without restarting buffered playback.')
s=s.replace('- [V590 release notes](../releases/PAFPlayer_v590_locked_bass_session_detection_release_notes.md)\n- [Locked-bass controls and verification](playback-controls.md#v590-lock-detection-and-restart-repair)',
            f'- [V591 release notes](../releases/{name}_release_notes.md)\n- [Live bass transitions and verification](playback-controls.md#v591-live-bass-transitions)')
write(path,s)
path='PAFPlayer.md';s=(root/path).read_text(encoding='utf-8')
s=s.replace('## Current source — V590',f'''## Current source — V591

- Lock/unlock bass reduction and web bass controls update the buffered audio
  stream without stopping its decoder or clearing queued sound.
- [Live bass behavior and manual verification](docs/playback-controls.md#v591-live-bass-transitions).
- [V591 release notes](releases/{name}_release_notes.md).

## Recent release — V590''',1)
write(path,s)
path='PAFPlayer_changelog.md';s=(root/path).read_text(encoding='utf-8')
s=s.replace('# PAFPlayer changelog\n',f'''# PAFPlayer changelog

## V591 — October 21, 2026

Remove the decoder-restart silence when locked-session bass reduction changes
on buffered WaveOut playback. Keep a named FFmpeg bass filter and send live gain
commands through a private pipe, retaining the same decoder, output queue and
playback clock. Route web bass controls and all selected output devices through
the same path. Preserve settings, shelf response and legacy FFplay fallback.
Real PCM continuity and muted native WaveOut checks passed; 69/70 relevant tests
passed with the previously recorded seek-test failure unchanged.
[Release notes](releases/{name}_release_notes.md).
''',1)
write(path,s)
notes=f'''# PAFPlayer V591 — live bass transitions

Released October 21, 2026.

Lock/unlock previously stopped FFmpeg and opened a new decoder/output stream to
change the bass shelf. That caused the reported silence despite the correct
V590 lock detection. V591 sends a live gain command to the buffered renderer's
existing named FFmpeg bass filter. The worker, decoder, WaveOut queue and device
clock stay intact. Web bass settings and multiple outputs use the same path.

The low-shelf response, setting IDs, saved values, command-line overrides,
one-second lock polling and official-instance ownership remain unchanged. No new
audio dependency is required. Playback settings were not changed during testing.
Legacy FFplay retains the same-position restart and its possible gap; the live
fix applies to buffered playback. Queued audio still delays audible updates.

## Validation

- 70 focused/relevant checks: **69 passed**, no errors or skips. The one failure,
  `test_seek_restarts_ffplay_at_requested_offsets`, expects three launches but
  receives two; the identical failure is recorded for V589 and V590.
- Eleven new tests cover live lock/unlock, legacy fallback, web changes, private
  stdin ownership, bounded numeric commands, repeated requests, worker routing,
  multiple outputs, unchanged clocks, and actual PCM continuity.
- Actual FFmpeg 4.2.3: 96 kHz, 8 channels, 24-bit; all **672,000 frames / 7 seconds**
  survived 0 → -14 → 0 dB changes, with audio present through both transitions
  and the final marker intact. Low-frequency attenuation measured -14.67 dB at
  40 Hz, with only +0.11 dB at 1 kHz; normal bass returned afterward.
- Real Windows WaveOut, muted: worker PID 74572 stayed unchanged at both gain
  changes, reached all six seconds, and reported **zero underruns**.
- Compilation of the source and 24 embedded modules, plus generated web
  JavaScript, is recorded in the V591 build report.
- No V591 listening/lock/unlock test has yet been performed. Restart your normal
  player to load this version, then follow the
  [manual check](../docs/playback-controls.md#v591-live-bass-transitions).

Reports: [tests](../tests/reports/v591-bass-checks-20261021-104104.json),
[muted native worker](../tests/reports/v591-native-muted-20261021-104335.json),
[initial FFmpeg protocol probe](../tests/reports/v591-ffmpeg-command-probe-20261021-103353.json).

Source SHA-256: `{sha}`.

## Files and deployment

The active workspace file and descriptive release copy contain identical Python
source. The versioned manual, changelog and playback documentation were updated.
Required backups were created and hash-verified before every replacement. A
complete path inventory is in `tests/reports/v591-change-manifest.json`.

**No literal C:\\BAT paths were changed.** `play_audio_file.py` was not modified.
The running household player was not restarted or sent playback commands. No
settings, UAC, installed package, or Windows lock configuration was changed.
'''
write('releases/'+name+'_release_notes.md',notes)
# These are copies, not edits to any existing release artifact.
for source_name,suffix in (('PAFPlayer.py','.py'),('PAFPlayer.md','.md')):
    data=(root/source_name).read_bytes();dest=root/'releases'/(name+suffix)
    with dest.open('xb') as stream: stream.write(data)
    assert hashlib.sha256(data).digest()==hashlib.sha256(dest.read_bytes()).digest()
    print('COPIED',dest)
