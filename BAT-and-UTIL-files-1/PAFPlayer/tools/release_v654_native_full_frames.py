"""Publish exact native full-frame formatting with evidence and path disclosure."""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from prepare_v642_artwork_chrome import ROOT,write,unique

def report(pattern):
    path=max((ROOT/'tests/reports').glob(pattern),key=lambda p:p.stat().st_mtime)
    return path,json.loads(path.read_text())
focused_path,focused=report('v654-checks-V654-*.json')
broad_path,broad=report('pipeline-regressions-V654-*.json')
_,baseline=report('pipeline-regressions-V651-*.json')
digest=hashlib.sha256((ROOT/'PAFPlayer.py').read_bytes()).hexdigest()
assert digest==focused['source_sha256']==broad['source_sha256']
assert focused['tests']==115 and len(focused['failures'])==2 and not focused['errors']
assert all('test_play_audio_file_v418.' in n for n,t in focused['failures'])
assert broad['tests']==188
for key in ('failures','errors'):assert {n for n,t in broad[key]}=={n for n,t in baseline[key]}
release=ROOT/'releases/PAFPlayer_v654_native_full_frame_formatting.py'
with release.open('xb') as f:f.write((ROOT/'PAFPlayer.py').read_bytes())
assert release.read_bytes()==(ROOT/'PAFPlayer.py').read_bytes()
notes=ROOT/'releases/PAFPlayer_v654_native_full_frame_formatting_release_notes.md';assert not notes.exists()
write(notes.relative_to(ROOT),f'''# PAFPlayer V654 — native full-frame artwork formatting

Released November 11, 2026. SHA-256: `{digest}`.

The user confirmed that V653 removed about 95% of the visualizer hitching but
tiny hangs remained during ordinary playback. The new V653 trace caught a
243 ms diagnostic delay near a full garbage collection. Three minutes of live
sampling reported 45.8–55.4 FPS toward 60, no popup backlog, and zero audio
underruns. Private memory ranged from 1.470 to 1.510 GB, ending at 1.498 GB.
This is a short observation, not proof of long-term stability or frame latency.

## Change

The artwork compositor already produced packed cells in native code, but the
full-frame path still iterated over every cell in Python to format foreground
and background terminal color strings. V654 reuses the existing native artwork
encoder for that step, then restores the original row strings exactly. Temporary
native cursor prefixes are stripped in memory; the existing caller still owns
all row positioning, wrapping, line erasure and character-set resets.

Semantic-only rendering still bypasses string encoding. Missing NumPy/native
support, invalid dimensions, native errors or malformed output retain the old
Python formatter. No new native binary, dependency, setting, frame target, audio
change, GC policy, or reduced image precision was introduced. V653 features and
V652's memory-retention fixes remain intact.

## Evidence

The repeat benchmark formats 200 dynamic 140×48-cell frames with the same output
digest: **5.503 ms/frame before, 0.657 ms/frame after**, about 8.4× faster for this
step. The old path triggered 12 generation-0 and one generation-1 collections;
the new path triggered none during that measured interval. These are isolated
formatting timings, not end-to-end FPS or proof that every hitch is eliminated.
Alternative integer/string cache keys were rejected because they slowed this
workload by 22–24%, despite reducing collections.

- [Production benchmark](../tests/reports/full-frame-native-20261111-102649.json)
- [V653 live stack trace](../tests/reports/v648-thread-stacks-20261111-101441.json)
- [V653 three-minute sample](../tests/reports/v652-live-retention-V653-20261111-101837.json)

All **eight new tests pass**, including 128 flag combinations, default flags,
multiple dimensions, repeated colors, semantic-only output, missing dependencies,
errors, malformed native output and empty/uneven rows. Full payloads, row strings
and semantic cells match the immutable V653 oracle exactly. The 115-test group
has 113 passes and two pre-existing media-coordinator failures. The 188-test group
has 176 passes, 11 failures and one source-contract error, matching its baseline.
Python compilation, 27 embedded/source comparisons and eight generated JavaScript
syntax checks pass. The suite is not wholly green.

- [Focused/relevant checks](../tests/reports/{focused_path.name})
- [Broad checks](../tests/reports/{broad_path.name})

## Manual verification

Restart the usual PAFPlayer.py with console karaoke, artwork popup and floating
lyrics enabled. Check ordinary animation, lyric-gap layout changes, the rightmost
artwork cells, frame position and glyph shapes. Verify that audio stays smooth.
Live V654 verification and a multi-hour memory observation remain pending.

The native ABI rejected a zero-length origin during the initial offline
experiment; the tested implementation supplies a temporary nonempty origin and
removes it before output. No experimental payload was sent to the live console.

Verified sibling backups are retained. Prior releases are preserved and no files
were permanently deleted. play_audio_file.py was not modified. No literal
C:\\BAT path changed. [All affected paths](../tests/reports/v654-change-manifest.json).
''')
p=ROOT/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf8');head='# PAFPlayer changelog\n\n';assert s.startswith(head)
write(p.relative_to(ROOT),head+'''## V654 — November 11, 2026

Reuse the existing native artwork encoder for full-frame row formatting with
byte-exact output and a Python fallback. The isolated 200-frame benchmark drops
from 5.50 to 0.66 ms per frame for this step. Eight new tests pass; the 115- and
188-test selections retain only baseline failures. Live smoothness remains to
be checked after restart.
[Release notes](../releases/PAFPlayer_v654_native_full_frame_formatting_release_notes.md).

'''+s[len(head):])
p=ROOT/'docs/performance-v519.md';s=p.read_text(encoding='utf8')
write(p.relative_to(ROOT),s+'''

## V654 native full-frame formatting

The user reported about 95% improvement with V653, with tiny remaining hangs in
ordinary playback. A three-minute live sample ranged from 1.470 to 1.510 GB of
private memory, ending at 1.498 GB, with no audio underruns or popup backlog.
An occasional diagnostic delay remained near GC; this is not frame timing.

V654 removes the per-cell Python color-formatting loop from native packed-artwork
full frames. It reuses the existing encoder and produces exactly the old row
strings, preserving terminal positioning and the dependency/error fallback.
The isolated formatting benchmark improved from 5.50 to 0.66 ms/frame; eight new
tests cover output parity and fallbacks. Existing test failures match baseline.
The slower alternative cache-key experiments were not adopted. Live V654
smoothness and long-session retention remain unverified until restart and use.
[Evidence and procedure](../releases/PAFPlayer_v654_native_full_frame_formatting_release_notes.md).
''')
p=ROOT/'docs/README.md';s=p.read_text(encoding='utf8')
start=s.index('Current release:');end=s.index('\n## ',start)
write(p.relative_to(ROOT),s[:start]+'''Current release: **V654** — faster full-frame artwork formatting with exact output and fallback behavior.
[Measurements, limitations, and verification](performance-v519.md#v654-native-full-frame-formatting).

'''+s[end:])
moves=[]
for pattern in ('benchmark_full_frame_native.py.bak.*.bak','test_v654_native_full_frames.py.bak.*.bak'):
    for backup in (ROOT/'tests').glob(pattern):
        target=unique(ROOT/'backups'/backup.name);h=hashlib.sha256(backup.read_bytes()).hexdigest()
        assert ROOT in backup.resolve().parents and ROOT in target.resolve().parents
        backup.rename(target);assert hashlib.sha256(target.read_bytes()).hexdigest()==h
        moves.append({'from':str(backup),'to':str(target),'status':'moved verified backup'})
for p in [release,*ROOT.glob('tests/*v654*.py'),ROOT/'tests/benchmark_full_frame_native.py',ROOT/'tests/benchmark_packed_sgr_keys.py',ROOT/'tests/probe_v652_live_retention.py',*ROOT.glob('tools/*v654*.py')]:
    compile(p.read_text(encoding='utf8'),str(p),'exec')
paths={ROOT/name:'modified' for name in ('PAFPlayer.py','docs/README.md','docs/PAFPlayer_changelog.md','docs/performance-v519.md')}
for folder,patterns in {'tests':['*v654*.py','benchmark_full_frame_native.py','benchmark_packed_sgr_keys.py','probe_v652_live_retention.py'],
    'tools':['*v654*.py'],'releases':['*v654*','PAFPlayer.py.bak.202611111025*.bak'],
    'backups':['*20261111102*.bak'],'docs':['*.bak.20261111102*.bak'],
    'tests/reports':['*20261111-101441*','*20261111-101837*','packed-sgr-keys-20261111-101950*','full-frame-native-20261111-102*','v654-checks-*','pipeline-regressions-V654-*']}.items():
    for pattern in patterns:paths.update({p:'created' for p in (ROOT/folder).glob(pattern)})
for pattern in ('full-frame-native-20261111-102*','v654-checks-*','pipeline-regressions-20261111-102*'):
    for stage in (ROOT/'tests/runs').glob(pattern):
        paths[stage]='created';paths.update({p:'created' for p in stage.rglob('*')})
manifest=ROOT/'tests/reports/v654-change-manifest.json'
entries=[{'path':str(p),'status':state,**({'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} if p.is_file() else {'kind':'directory'})} for p,state in sorted(paths.items(),key=lambda x:str(x[0]))]
entries.append({'path':str(manifest),'status':'created'})
with manifest.open('x',encoding='utf8') as f:json.dump(dict(version='V654',source_sha256=digest,release_matches=True,
    live_verification_pending=True,paths=entries,moves=moves,literal_cbat_changes=[],deleted_paths=[],
    roots={str(r):sorted(p.name for p in r.iterdir()) for r in (ROOT,ROOT/'lockscreen',ROOT/'screensaver')}),f,indent=2)
print(release);print('SHA256',digest);print(manifest)
