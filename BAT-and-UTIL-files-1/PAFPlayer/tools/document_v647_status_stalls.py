"""Document the narrow status-publisher fix with verified replacement backups."""
import hashlib
from prepare_v642_artwork_chrome import ROOT, write

source=ROOT/'PAFPlayer.py'
release=ROOT/'releases/PAFPlayer_v647_status_publication_stalls.py'
assert source.read_bytes()==release.read_bytes()
assert hashlib.sha256(source.read_bytes()).hexdigest()=='df8d90d57b353b976df7e7cff4a88b2f256efc4b43b880214120aa442c1aa6a8'
notes='PAFPlayer_v647_status_publication_stalls_release_notes.md'
assert not (ROOT/'releases'/notes).exists()
write('releases/'+notes, '''# PAFPlayer V647 — periodic status publication stalls

Released November 9, 2026.

## Diagnosis and change

The reported symptom is smooth rendering interrupted by console-only freezes;
audio continues. A live V646 performance sample measured web-status preparation
at 133–237 ms per publication, taking 40–61% of the sample window. The retained
trace includes the 133 ms / 40% sample. This work runs between visualizer frames.
V646's emoji-mask improvement did not measure or address this periodic work.

The publisher reloaded all 111 persisted settings twice, just to report title
style and title content. Registry operations repeatedly release/reacquire the
Python interpreter lock. Under competing Python rendering, the waiting between
those operations can dominate their own I/O cost. A separate-process fixture
reproduced that effect with the actual two production expressions: roughly
4.14 ms when quiet versus 2,229 ms with a continuously busy Python worker.
This synthetic contention case is more severe than the sampled live player.

V647 reports the live `console_title_style` and `console_title_content` already
maintained by controls and default changes. In the same fixture the expressions
took about 0.002 ms under contention and performed zero settings reloads.
There is no TTL cache or stale-value delay. Shape/coloring fields remain
consistent with the same live title style. Configuration IDs stay unchanged.

Only these two value expressions and version/build labels changed. An AST
comparison confirms the rest of the playback function is identical to V646.
Audio, queue ownership, console encoding, karaoke effects/sizing, popup window
behavior, and V646's color-search improvement are preserved.

## Validation and limits

**132 relevant tests: 125 passed, seven failed, no errors/skips.** The same seven
historical tests fail in V646. Three new tests check that periodic publication
never loads bulk settings, all style/content combinations are current, and
existing clock/lyric/control fields remain present. All 27 bundled modules
match their editable sources; Python compilation and eight web scripts pass.
This is a relevant subset, not a claim that the entire historical suite passes.

The external nonblocking profiler could not attach because Windows denied
process access. The player's existing performance HUD supplied the live timing.
It was briefly enabled for measurement and confirmed off afterward; playback
was not commanded, and no persistent settings were changed. The downloaded
py-spy wheel/binary/license are retained only in the isolated test fixture.

The benchmarks establish removal of a blocking path; they do not establish
full-player FPS or prove that every possible stall is gone. Live V647 validation
with all three lyric displays remains pending a player restart and observation.

[Live V646 trace](../tests/reports/v647-live-components-20261109-071627.json) ·
[V646 contention fixture](../tests/reports/v647-status-contention-V646-20261109-072155.json) ·
[V647 contention fixture](../tests/reports/v647-status-contention-V647-20261109-072256.json) ·
[Checks](../tests/reports/v647-checks-V647-20261109-072329.json) ·
[Comparison](../tests/reports/v647-comparison.json)

## Manual verification

Restart the usual player from the updated workspace (and older remote tray
clients), keeping console, artwork popup, and floating lyrics enabled. Use the
same terminal size/settings and timed-lyric track. Watch repeated lyric changes,
instrumental gaps, and normal controls. Compare several completed five-second
performance windows; the web-status component should no longer show the bulk
settings delay. Check visual continuity, not just average FPS. Verify title
style/content changes still appear in the web interface immediately.

Reproduce isolated checks/benchmarks from the project directory:

```powershell
& C:\\ProgramData\\anaconda3\\python.exe -B -X utf8 tests\\verify_v647_status_stalls.py
& C:\\ProgramData\\anaconda3\\python.exe -B -X utf8 tests\\benchmark_v647_status_stalls.py
```

The verifier returns failure for the seven retained historical failures; none
are hidden. Optional benchmark argument 1 is the older release source path.

The release copy is new and matches the tested active source. SHA-256:
`df8d90d57b353b976df7e7cff4a88b2f256efc4b43b880214120aa442c1aa6a8`.
Required sibling backups were verified and retained. Project, lockscreen, and
screensaver root audits found only active inputs/runtime files. No deletion or
cleanup move was needed. No literal C:\\BAT paths changed; play_audio_file.py
was not edited. See tests/reports/v647-change-manifest.json for the path inventory.
''')
readme=(ROOT/'docs/README.md').read_text(encoding='utf-8')
old='Current release: **V646** — lower karaoke rendering load and fewer duplicate artwork repaints.\n[Measurements, limitations, and verification](performance-v519.md#v646-karaoke-render-load).'
assert old in readme
write('docs/README.md',readme.replace(old,'Current release: **V647** — remove bulk settings reloads that stall periodic visualizer updates.\n[Measurements, limitations, and verification](performance-v519.md#v647-periodic-status-stalls).',1))
changelog=(ROOT/'docs/PAFPlayer_changelog.md').read_text(encoding='utf-8')
head='# PAFPlayer changelog\n\n';assert changelog.startswith(head)
write('docs/PAFPlayer_changelog.md',head+'''## V647 — November 9, 2026

Use the live title style/content in periodic web status instead of loading all
111 saved settings twice on the visualizer thread. Live V646 timings identified
133–237 ms status preparation; a contention fixture reproduces the registry/GIL
delay and confirms zero bulk reads after the change. No other playback or
rendering behavior changes. 125/132 relevant tests pass, with the same seven
historical failures as V646, plus compilation, 27-module parity, and eight web
script checks. Live V647 continuity remains to be checked after restart.
[Release notes](../releases/PAFPlayer_v647_status_publication_stalls_release_notes.md).

'''+changelog[len(head):])
performance=(ROOT/'docs/performance-v519.md').read_text(encoding='utf-8')
write('docs/performance-v519.md',performance+'''

## V647 periodic status stalls

The V646 helper optimization did not address long pauses between otherwise
smooth frames. Live timers found periodic web-status preparation taking
133–237 ms/update. Two title fields each triggered a complete reload of 111
persisted settings on the playback/visualizer loop. Those registry calls also
repeatedly yield the interpreter lock, allowing competing rendering work to
amplify the delay. A synthetic busy-Python-thread fixture reproduces this:
the actual expressions took 4.14 ms quiet and 2,229 ms under sustained contention.

V647 uses the two current in-memory title values already maintained by control
and default changes. There are zero bulk settings reads and no polling/cache
delay; the fixture measures about 0.002 ms under contention. Only those two
expressions and release labels differ from V646. Effects and audio are unchanged.

125 of 132 relevant tests pass; seven existing failures match V646. All bundled
sources, Python compilation, and generated web scripts validate. Benchmark
results demonstrate the removed blocking path, not guaranteed FPS. Live V647
continuity with all three lyric displays remains pending restart/observation.
[Evidence, reproducible commands, and manual checks](../releases/PAFPlayer_v647_status_publication_stalls_release_notes.md).
''')
print('Documented V647; live validation remains explicitly pending.')
