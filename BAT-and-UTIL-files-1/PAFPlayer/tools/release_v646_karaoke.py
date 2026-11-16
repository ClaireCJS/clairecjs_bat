"""Verify evidence and publish a non-overwriting workspace release with backups."""
import ast
import hashlib
import json
from pathlib import Path
from prepare_v642_artwork_chrome import ROOT, write, unique


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    reports = ROOT/'tests/reports'
    candidate = json.loads((reports/'v646-checks-20261109-011750.json').read_text())
    baseline = json.loads((reports/'v646-checks-V645-20261109-011937.json').read_text())
    old_time = json.loads((reports/'v646-profile-V645-20261109-011444.json').read_text())
    new_time = json.loads((reports/'v646-profile-V646-20261109-011558.json').read_text())
    path = ROOT/'PAFPlayer.py'
    assert sha(path) == candidate['source_sha256'] == new_time['source_sha256']
    assert sha(ROOT/'releases/PAFPlayer_v645_artwork_window_controls.py') == baseline['source_sha256'] == old_time['source_sha256']
    failures = lambda r: {name for name, _ in r['failures']}
    assert failures(candidate) == failures(baseline) and len(failures(candidate)) == 7
    assert candidate['tests'] == 129 and baseline['tests'] == 119
    assert not candidate['errors'] and not baseline['errors']
    assert candidate['bundles'] == len(candidate['parity']) == 27 and candidate['javascript_blocks'] == 8
    assert not old_time['profiled'] and not new_time['profiled']
    timing = []
    for old, new in zip(old_time['results'], new_time['results']):
        assert old['name'] == new['name']
        for field in ('sha256', 'value'):
            assert old.get(field) == new.get(field), (old['name'], field)
        timing.append(dict(name=old['name'], before_ms=old['median_ms'], after_ms=new['median_ms']))
    comparison = unique(reports/'v646-comparison.json')
    with comparison.open('x', encoding='utf-8') as f:
        json.dump(dict(baseline_tests=119, current_tests=129, current_passes=122,
                       unchanged_failures=sorted(failures(candidate)), new_failures=[],
                       profiled=False, output_hashes_match=True, timings=timing), f, indent=2)

    source = path.read_text(encoding='utf-8')
    release = unique(ROOT/'releases/PAFPlayer_v646_karaoke_render_load.py')
    with release.open('xb') as f:
        f.write(path.read_bytes())
    assert sha(release) == sha(path)
    notes = unique(ROOT/'releases/PAFPlayer_v646_karaoke_render_load_release_notes.md')
    write(notes.relative_to(ROOT), f'''# PAFPlayer V646 — karaoke render load

Released November 9, 2026.

Inherited Emojimaxx answer colors used a Python pixel-by-pixel search on every
refresh. A colored emoji can leave its monochrome glyph mask completely empty,
forcing two whole-region scans. Large expanded lyrics made this expensive on
the shared interpreter while console, artwork, and floating lyrics ran together.

V646 uses Pillow's native mask operations to find the same color. It retains
the original thresholds, leftmost-column selection, center-row tie breaking,
clipping, and fallback. It reads at most one pixel through Python. No new cache,
frame queue, process, setting, or dependency is introduced.

Artwork draws a new lyric immediately, cancels the previous animation timer,
and waits its normal 50/90/140/150/220 ms cadence before recoloring. This avoids
the old zero-delay second repaint. Console refresh limits, lyric clocks,
playback/audio code, font fitting, effects, and configuration IDs stay intact.

## Measurements and checks

Unprofiled synthetic inherited-color lookup medians, measured on this computer:

| Region | V645 | V646 |
| --- | ---: | ---: |
| Empty emoji mask, 300 × 160 | 49.10 ms | 0.061 ms |
| Empty emoji mask, 900 × 320 | 332.00 ms | 0.269 ms |
| Left padding, 300 × 160 | 8.06 ms | 0.341 ms |
| Left padding, 900 × 320 | 53.17 ms | 1.787 ms |

Both artwork image hashes and all selected colors match. These are helper
timings, not achieved FPS. Large-image Tk uploads still cost about 28 ms in the
1920-wide fixture; other render/terminal costs and game load remain possible.
The November 6 profile identified the hotspot but has profiler overhead; the
table uses the November 9 unprofiled comparison only.

**129 relevant tests: 122 passed, seven failed, zero errors/skips.** The same
seven failures occur on unchanged V645 (112 passed out of 119). Ten new tests
pass, including 300 deterministic color-equivalence cases, bounded pixel calls,
timer cancellation, immediate cues, and unchanged size-dependent cadence.
Older failing tests concern historical UI/source contracts and removal counts;
they are retained and are not reported as passing. This is a relevant subset,
not the complete historical suite. All 27 module/source parity comparisons,
Python compilation, and eight generated web-script syntax checks pass.

Tests use preserved isolated fixtures. Guards blocked attempted live registry
and C:\\logs writes from older tests. No live playback commands or preferences
were changed. [Comparison report](../tests/reports/{comparison.name});
[current checks](../tests/reports/v646-checks-20261109-011750.json);
[baseline checks](../tests/reports/v646-checks-V645-20261109-011937.json).

## Try the release

Restart PAFPlayer from the updated workspace, and update/restart any remote
tray client that renders lyrics. Enable console, artwork, and floating lyrics;
use a timed song with Emojimaxx answers and inherited answer coloring. Compare
FPS and visible stalls at the same window sizes/settings, including full-size
artwork, repeated lyric changes, pause/resume, and seeking. Confirm all three
displays remain synchronized and answer colors still match their settings.
Live sustained FPS with all three displays has not yet been verified.

The new release copy is `{release.name}` and matches the tested active source:
SHA-256 `{sha(path)}`.

Verified sibling backups precede replacements and are retained in the required
archives. Root audits of PAFPlayer, lockscreen, and screensaver found only active
inputs/runtime sidecars; nothing required deletion or relocation.
No literal C:\\BAT paths changed. `play_audio_file.py` is unchanged.
The full path inventory is `tests/reports/v646-change-manifest.json`.
''')
    readme = (ROOT/'docs/README.md').read_text(encoding='utf-8')
    old = 'Current release: **V645** — artwork border resize cursors and a focus-only maximize/restore button.'
    assert old in readme
    write('docs/README.md', readme.replace(old,
        'Current release: **V646** — lower karaoke rendering load and fewer duplicate artwork repaints.\n'
        '[Measurements, limitations, and verification](performance-v519.md#v646-karaoke-render-load).', 1))
    changelog = (ROOT/'docs/PAFPlayer_changelog.md').read_text(encoding='utf-8')
    heading = '# PAFPlayer changelog\n\n'
    assert changelog.startswith(heading)
    write('docs/PAFPlayer_changelog.md', heading + f'''## V646 — November 9, 2026

Replace the per-pixel Python search for inherited Emojimaxx answer colors with
native Pillow mask operations, preserving exact color selection. The large
empty-mask fixture falls from 332 ms to 0.269 ms. Cancel old artwork animation
timers at new cues and remove the immediate redundant repaint; cue delivery and
normal animation cadence remain intact. 122/129 relevant tests pass; all seven
failures also occur on V645. No new failures, 27-module parity, compilation, and
eight JavaScript syntax checks pass. Live all-display FPS remains unverified.
[Release notes](../releases/{notes.name}).

''' + changelog[len(heading):])
    performance = (ROOT/'docs/performance-v519.md').read_text(encoding='utf-8')
    write('docs/performance-v519.md', performance + f'''

## V646 karaoke render load

With console, artwork, and floating lyrics enabled, inherited Emojimaxx answer
colors caused repeated Python scans across lyric masks. Colored emoji can leave
an empty region in the monochrome mask; a 900 × 320 region took 332 ms to reject.
V646 performs the search in Pillow's native mask operations, reducing that case
to 0.269 ms and a padded glyph case from 53.17 ms to 1.787 ms. The selected colors
and artwork image hashes remain identical. No quality/cadence setting changed.

New artwork cues still paint immediately. Their old animation timers are
cancelled, and the next color tick waits its usual interval instead of painting
the same fresh layer again at zero delay. Console lyrics retain their existing
refresh limit. No audio, decoder, playback queue, or lyric clock change is part
of this release. Both local and remote tray popup renderers get the shared fix.

The unprofiled synthetic measurements demonstrate reduced helper cost, not a
guaranteed live FPS. Full-size Tk bitmap uploads remain a separate expense
(about 28 ms in the 1920-wide fixture). Live sustained performance with all
three displays and simultaneous gaming remains a manual check after restart.

129 relevant tests were run: 122 passed; seven historical failures reproduce on
V645. Ten new tests include 300 equivalent color cases and animation scheduling.
All 27 bundled sources match, compilation succeeds, and eight web scripts parse.
[Release notes and manual procedure](../releases/{notes.name}) and
[comparison evidence](../tests/reports/{comparison.name}).

From the project directory, run the guarded checks and optional benchmark:

```powershell
& C:\\ProgramData\\anaconda3\\python.exe -B -X utf8 tests\\verify_v646_karaoke_render_load.py
& C:\\ProgramData\\anaconda3\\python.exe -B -X utf8 tests\\benchmark_v646_karaoke.py
```

The verifier deliberately returns a failing exit status for the seven retained
historical failures; it does not hide them. Benchmark profiling is off by
default; set `PAF_PROFILE_KARAOKE=1` only to diagnose call costs, not for timings.
Fixtures are retained under `tests/runs`, and reports under `tests/reports`.
''')
    # Final source/build agreement, without rewriting bytecode or live files.
    for p in [path, release, *ROOT.glob('tests/*v646*.py'), *ROOT.glob('tools/*v646*.py')]:
        compile(p.read_text(encoding='utf-8'), str(p), 'exec')
    assert source == release.read_text(encoding='utf-8')
    for p in (ROOT/'docs/README.md', ROOT/'docs/PAFPlayer_changelog.md', notes):
        assert 'V646' in p.read_text(encoding='utf-8')
    print('RELEASE', release, sha(release))


if __name__ == '__main__':
    main()
