"""Publish the tested karaoke-resize optimization and preserve replaced docs."""
import hashlib
import json
from prepare_v642_artwork_chrome import ROOT,write

report=ROOT/'tests/reports/v650-checks-V650-20261110-013954.json'
baseline=ROOT/'tests/reports/v650-checks-V649-20261110-013750.json'
current=json.loads(report.read_text());old=json.loads(baseline.read_text())
focused=json.loads((ROOT/'tests/reports/v650-checks-V650-20261110-013454.json').read_text())
digest=hashlib.sha256((ROOT/'PAFPlayer.py').read_bytes()).hexdigest()
assert digest==current['source_sha256']==focused['source_sha256']
assert current['tests']==old['tests']==188
assert {n for n,t in current['failures']}=={n for n,t in old['failures']}
assert {n for n,t in current['errors']}=={n for n,t in old['errors']}
assert len(current['failures'])==11 and len(current['errors'])==1
assert focused['tests']==198
assert not any('test_v650_karaoke_resize.' in n for n,t in focused['failures']+focused['errors'])
release=ROOT/'releases/PAFPlayer_v650_karaoke_resize.py'
with release.open('xb') as f:f.write((ROOT/'PAFPlayer.py').read_bytes())
assert release.read_bytes()==(ROOT/'PAFPlayer.py').read_bytes()
notes=ROOT/'releases/PAFPlayer_v650_karaoke_resize_release_notes.md';assert not notes.exists()
write(notes.relative_to(ROOT),f'''# PAFPlayer V650 — reduce karaoke-resize stalls

Released November 10, 2026.

After V649, the user reported mostly fluid rendering, with a large remaining
hitch specifically when the three double-height karaoke lines disappear/return
and the visualizer expands/contracts. The V649 transition trace caught roughly
1.5 seconds on the playback thread re-extracting/fingerprinting artwork and
quantizing its cells for a new height. This is distinct from the library lock
and per-poll registry reads fixed in V649.
[Captured transition](../tests/reports/v650-karaoke-transition-V649-20261109-135114.json).

## Changes

- Reuse one track's encoded cover variants across compact, expanded and
  microtile grids. Retention is capped at 32 MiB; oversized sources remain usable
  but are not cached. A different source signature replaces the entry. Source
  extraction is outside the short cache lock, and concurrent extraction keeps
  using the existing single-flight mechanism.
- For the fixed-DRCS seam strategy used in the trace (strategy 5), perform the
  expensive two-color cell quantization with NumPy in 256-cell batches. The
  scalar pair ordering, tie handling, half-to-even rounding, foreground luma and
  downloaded glyph selection are preserved. NumPy absence and other strategies
  retain the existing scalar path. Existing bounded geometry caches retain the
  converted results when returning to a height.

No worker, setting, configuration ID, playback command, font-bank policy, console
encoding or layout behavior was added or changed. Karaoke still disappears in
gaps and the visualizer still fills its rows. The playback owner function is
AST-identical to V649. No audio-processing code changed.

## Evidence and checks

The deterministic cold-cache benchmark uses 140 columns, 42/48 rows and both
background/bar strengths. Scalar conversion took 599–687 ms per layer. The new
path took 89–101 ms after first-use NumPy setup (the first case took 195 ms).
Returning to a cached grid took about 0.003 ms. All four resulting grids matched
the scalar output exactly. These are conversion timings, not end-to-end FPS or
proof that every visible transition is smooth.
[Benchmark](../tests/reports/v650-resize-benchmark-20261110-013413.json).

All **10 new tests pass**, including 156 detail-mode/layout/strength combinations,
uniform colors, distance ties, rounding, sample geometry, fallback, bounded
retention, reuse across four layouts, source replacement and extraction errors.
The **188 existing-test run has 176 passes, 11 failures and one error**, exactly
matching V649. The expanded selection includes artwork/DRCS, seam, transport,
karaoke, popup, diagnostics and workflow tests. Python compilation, 27 bundled
source comparisons and eight generated JavaScript syntax checks pass.

The earlier combined 198-test runs additionally timed out in the existing
five-second silent-playback test. That test passes alone and in V650's clean
188-test comparison; the timeout depends on test ordering. It remains recorded
as a test-isolation limitation, not silently removed or presented as a fully
green suite. One run also emitted Tk's asynchronous-thread cleanup diagnostic.
No new test failed after the zero-brightness edge case was corrected.

- [V650 existing tests](../tests/reports/v650-checks-V650-20261110-013954.json)
- [V649 comparison](../tests/reports/v650-checks-V649-20261110-013750.json)
- [Combined run / focused tests](../tests/reports/v650-checks-V650-20261110-013454.json)
- [Isolated silent-playback pass](../tests/reports/v650-silence-V650-20261110-013706.json)

The test guards blocked attempted writes to live registry/log/history locations.
No literal C:\\BAT paths were changed. Live visual verification of V650 remains
pending restart and feedback; do not describe the overall lag issue as fully fixed.

## Manual verification

Restart the usual player from PAFPlayer.py with console karaoke, artwork popup,
and floating lyrics enabled. Use a song with timed lyrics and gaps longer than
the six-second outgoing lyric fade. Check both the first shrink/expand and later
returns to each height. Confirm the artwork and glyph shapes are unchanged,
lyrics remain synchronized, and audio continues through transitions. Steam's
enabled load reduction still halves the frame target while a game is running.

`tests/probe_v650_karaoke_transitions.py` can collect a read-only 45-second local
trace, retaining cue presence/timing and thread locations without issuing playback
commands or changing settings. Its sampling adds overhead.

Release SHA-256: `{digest}`. The release copy equals tested PAFPlayer.py.
Verified sibling backups were archived; prior releases were preserved.
Project/lockscreen/screensaver roots were audited and need no cleanup move.
play_audio_file.py was not edited. No existing files were deleted.
[Complete affected-path audit](../tests/reports/v650-change-manifest.json).
''')
p=ROOT/'docs/README.md';s=p.read_text(encoding='utf-8')
old='Current release: **V649** — separate library scanning from event/HUD updates and remove settings reads from empty input polls.\n[Measurements, limitations, and verification](performance-v519.md#v649-library-lock-and-input-poll-stalls).'
assert old in s
write(p.relative_to(ROOT),s.replace(old,'Current release: **V650** — reduce artwork rebuilding when karaoke appears/disappears and the visualizer changes height.\n[Measurements, limitations, and verification](performance-v519.md#v650-karaoke-resize-stalls).',1))
p=ROOT/'docs/PAFPlayer_changelog.md';s=p.read_text(encoding='utf-8');head='# PAFPlayer changelog\n\n';assert s.startswith(head)
write(p.relative_to(ROOT),head+'''## V650 — November 10, 2026

Reduce the large artwork rebuild when the three-line karaoke area appears or
disappears. Reuse one bounded cover source across heights and batch fixed-DRCS
cell conversion without changing pixels, glyphs or layout. Cold conversion is
about 6–7 times faster after NumPy setup in the synthetic benchmark. Ten new
tests pass; 188 existing tests match V649's 11 failures and one error. The
combined suite's order-sensitive silent-playback timeout is documented. Live
resize smoothness still needs confirmation after restart.
[Release notes](../releases/PAFPlayer_v650_karaoke_resize_release_notes.md).

'''+s[len(head):])
p=ROOT/'docs/performance-v519.md';s=p.read_text(encoding='utf-8')
write(p.relative_to(ROOT),s+'''

## V650 karaoke resize stalls

V649 was reported mostly fluid, with a remaining large hitch when karaoke's six
physical rows are reclaimed or restored. A transition trace caught artwork
extraction/fingerprinting and Python cell quantization on the playback thread.
V650 reuses one source (32 MiB maximum) across geometry changes and batches the
fixed-DRCS seam strategy's quantization in NumPy with exact scalar parity. It
keeps the existing optional-dependency fallback and all other seam strategies.
No worker or audio change was added; the expansion/collapse behavior is retained.

Synthetic cold conversion dropped from 599–687 ms per layer to 89–101 ms after
first-use NumPy setup; the first optimized case took 195 ms. This is not a live
FPS measurement. Ten new tests pass and the 188-test comparison matches V649's
11 old failures and one error. A combined-suite silent-playback timeout passes
in isolation and is retained as a test-order limitation. Compilation, bundle
parity and JavaScript syntax checks pass. Live transition feedback is pending.
[Evidence and verification procedure](../releases/PAFPlayer_v650_karaoke_resize_release_notes.md).
''')
for p in [release,*ROOT.glob('tools/*v650*.py'),*ROOT.glob('tests/*v650*.py')]:
    compile(p.read_text(encoding='utf-8'),str(p),'exec')
print(release,digest)
