"""Publish the verified fit-to-window release, preserving existing artifacts."""
import hashlib
import json
from prepare_v642_artwork_chrome import ROOT, write, unique


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


source = ROOT / 'PAFPlayer.py'
report = max((ROOT/'tests/reports').glob('v643-checks-*.json'), key=lambda p: p.stat().st_mtime)
checks = json.loads(report.read_text(encoding='utf-8'))
assert checks['version'] == 'V643' and checks['source_sha256'] == sha(source)
assert checks['tests'] == 36 and not checks['failures'] and not checks['errors'] and not checks['skipped']
assert checks['bundles'] == len(checks['parity']) == 27 and checks['javascript_blocks'] == 8
assert not checks['blocked_writes']
name = 'PAFPlayer_v643_artwork_karaoke_fit'
for suffix in ('.py', '_release_notes.md'):
    assert not (ROOT/'releases'/(name+suffix)).exists(), 'Never replace a release'

section = '''## V643 artwork karaoke fills the window

Artwork karaoke now chooses the largest font that fits the available artwork
canvas beneath the title/web-button bar. Short cues grow; long cues wrap and
shrink as needed. Resizing the window recalculates the fit. Both the native Tk
renderer and the Pillow renderer used for colored emoji and timed effects use
the full canvas, with margins for shadows and enabled Emojimaxx answers.

The previous search stopped at 8.5% of the smaller window dimension, capped at
260 points. That was a starting-size ceiling, so even a short lyric could remain
small in a large window. V643 searches up to the available height, with the
existing logarithmic search and cached fonts. Pixel-rendered lyrics no longer
get an extra monitor-DPI multiplier on top of their pixel dimensions.

At the default 100% zoom the lyric fills whichever dimension limits its fit.
Ctrl+wheel / Ctrl+- reduce the fitted size to as little as 50%; Ctrl+= restores
it up to 100%. Older saved zoom values above 100% are accepted as full fit, and
the first zoom-out immediately reduces them. Settings IDs and storage stay
compatible. An intentionally saved zoom below 100% still makes lyrics smaller.
The song-title/web-button bar and its focus/border behavior are unchanged.

After restarting V643, enable artwork karaoke and try a short lyric, a long
lyric, and an Emojimaxx lyric with answers above/below it. Resize the popup to
wide and tall shapes: text should grow/wrap within the artwork area without
covering the header or clipping. Use Ctrl+= if a previously reduced zoom is
still active. Remote tray computers need their own updated copy and restart.

Verification: 36 focused and related tests pass with no skips. They exercise
actual Windows Tk font/canvas bounds and Pillow masks, portrait/landscape/4K
sizes, manual zoom, mixed emoji and answer spacing, native solid/rainbow/pattern
drawing, and the V642 header/border checks. All 27 bundled modules compile and
match their editable sources; all eight generated web scripts pass syntax
checks. A pre-fix test run reproduced the small-cue size ceiling. No playback
or live preferences were changed; live-song visual confirmation remains manual.

'''
p = 'docs/window-shortcuts.md'
s = (ROOT/p).read_text(encoding='utf-8')
s = s.replace('## V642 artwork popup header and focus border', section+'## V642 artwork popup header and focus border', 1)
write(p, s)
p = 'docs/README.md'
s = (ROOT/p).read_text(encoding='utf-8')
s = s.replace('Current release: **V642** — one-row artwork popup header, one web button, and an invisible inactive border.',
              'Current release: **V643** — artwork karaoke expands to fit the available window.')
s = s.replace('[Artwork popup header, borders, and window shortcuts](window-shortcuts.md#v642-artwork-popup-header-and-focus-border)',
              '[Artwork karaoke sizing, popup header, and window shortcuts](window-shortcuts.md#v643-artwork-karaoke-fills-the-window)')
s = s.replace('[Current V642 release notes](../releases/PAFPlayer_v642_artwork_popup_chrome_release_notes.md)',
              f'[Current V643 release notes](../releases/{name}_release_notes.md)')
write(p, s)
p = 'docs/PAFPlayer_changelog.md'
s = (ROOT/p).read_text(encoding='utf-8')
s = s.replace('# PAFPlayer changelog\n', f'''# PAFPlayer changelog

## V643 — November 5, 2026

Expand artwork karaoke to the largest size that fits its canvas, replacing the
8.5%-of-window/260-point ceiling in both native and Pillow rendering. Account
for shadows during wrapping and reserve space for enabled emoji answers.
Preserve manual zoom below full fit, old setting IDs, efficient binary search,
and V642's header/borders. All 36 focused/related tests pass, including actual
Tk canvas bounds and Pillow masks through 4K. Compilation, 27-module source
parity, and all eight web script syntax checks pass.
[Release notes](../releases/{name}_release_notes.md).
''', 1)
write(p, s)
notes = f'''# PAFPlayer V643 — artwork karaoke fit

Released November 5, 2026.

Artwork karaoke now expands to the largest fitting size inside the canvas
below the header. The prior 8.5%-of-window/260-point ceiling kept short cues
small. Both native vector text and Pillow text now fit the available space,
reserve shadow and emoji-answer margins, and wrap longer cues. Font fitting
remains logarithmic; cached fonts and the native rendering fast path remain.

Default 100% zoom means full fit. Existing zoom shortcuts reduce the fitted
size down to 50% or restore it up to 100%. Saved values above 100% are accepted
as full fit; one zoom-out immediately reduces them. No configuration IDs or
stored preference formats changed. The title/web-button bar stays unchanged.

## Verification

- **36 tests pass, zero failures/errors/skips**: short/long cues, real Tk font
  and canvas bounds, Pillow masks, colored/monochrome emoji, answer spacing,
  manual zoom, 4K growth, bounded fitting work, native rendered text/shadows,
  and relevant V642 header/geometry and V641 solution-color regressions.
- The same new sizing tests reproduced the issue against V642 before editing.
- Python compilation and all **27 embedded-module/source parity** checks pass;
  all **eight generated JavaScript blocks** pass Node syntax checks.
- No audio, household-player commands, or live preferences changed. Test GUI
  assertions ran on the isolated Windows test desktop; live-song visual
  verification after restart remains manual.

[Test report](../tests/reports/{report.name}) ·
[Behavior and manual verification](../docs/window-shortcuts.md#v643-artwork-karaoke-fills-the-window)

Restart the player, and any remote tray client using its own copy, to load
V643. If old manual zoom is below 100%, Ctrl+= restores full expansion.

Source SHA-256: `{sha(source)}`.

## Files

The release copy is new and hash-identical to the tested active source.
Required sibling backups were verified before replacement, then archived as
required. Root audits found only active code, project inputs and runtime/user
sidecars in PAFPlayer, lockscreen and screensaver. No deletions or cleanup moves
were needed. `play_audio_file.py` is unchanged. **No literal C:\\BAT paths changed.**
The complete file inventory is in `tests/reports/v643-change-manifest.json`.
'''
write('releases/'+name+'_release_notes.md', notes)
release = ROOT/'releases'/(name+'.py')
with release.open('xb') as f:
    f.write(source.read_bytes())
assert sha(release) == sha(source)

# Include retained failing baseline, passing runs, fixtures, and required backups.
modified = ['PAFPlayer.py', 'docs/README.md', 'docs/window-shortcuts.md', 'docs/PAFPlayer_changelog.md']
paths = {ROOT/p for p in modified}
for folder in ('tests', 'tools', 'releases', 'docs', 'backups'):
    for p in (ROOT/folder).rglob('*'):
        if p.is_file() and ('v643' in p.name.lower() or '.bak.20261105' in p.name
                           or any('v643-' in part for part in p.parts)):
            paths.add(p)
manifest = unique(ROOT/'tests/reports/v643-change-manifest.json')
payload = dict(version='V643', source_sha256=sha(source), release_sha256=sha(release),
               paths=[dict(path=str(p), status='modified' if p.relative_to(ROOT).as_posix() in modified else 'created',
                           sha256=sha(p)) for p in sorted(paths)],
               root_audits={part:[p.name for p in (ROOT/part).iterdir() if p.is_file()]
                            for part in ('', 'lockscreen', 'screensaver')},
               literal_c_bat_changes=[], deleted=[],
               backup_archives='PAFPlayer.py sibling backups moved to releases; changelog backup moved to backups; other backups remain siblings.')
with manifest.open('x', encoding='utf-8') as f:
    json.dump(payload, f, indent=2)
print('RELEASE', release, sha(release))
print('MANIFEST', manifest, len(paths), 'paths')
