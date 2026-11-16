"""Publish the checked artwork popup change without overwriting any release."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from prepare_v642_artwork_chrome import write

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=ROOT/'tests/reports/v642-checks-20261104-084801.json'
checks=json.loads(report.read_text(encoding='utf-8'))
source=ROOT/'PAFPlayer.py'
assert checks['source_sha256']==sha(source)
assert checks['tests']==25 and not checks['failures'] and not checks['errors']
assert checks['bundles']==len(checks['parity'])==27 and checks['javascript_blocks']==8
assert sha(ROOT/'tests/runs/artwork-v642-20261104-084825/PAFPlayer.py')==sha(source)
name='PAFPlayer_v642_artwork_popup_chrome'
for suffix in ('.py','_release_notes.md'):
    assert not (ROOT/'releases'/(name+suffix)).exists(),'Never overwrite an existing release'

section='''## V642 artwork popup header and focus border

The Artwork Pop-Up now has one row: a large **Artist - Song** title with a single
**🌐** button beside it. The button opens the player's web interface directly at
**Artwork** (`#artworkPopupSection`), including when a tray client points at a
remote player or a non-default web port. The header remains visible when the
popup loses focus. Long titles shorten with an ellipsis instead of shrinking
the font or pushing the web button offscreen.

The native Windows caption, resize frame and shadow are removed for the
window's entire lifetime. This fixes the second title overlapping the header
and the remaining gray Windows frame. Only PAFPlayer's own thin focus border
appears while the artwork window is active; it becomes transparent on focus
loss. Focus changes do not recreate the window or alter its geometry.

- Drag the song title to move the popup. Focus the popup, then drag a border
  or corner to resize it; Ctrl keeps a square resize.
- Right-click the song title for **Always on top** and **Close artwork popup**.
  Alt+F4 also closes the artwork popup. Taskbar/Alt-Tab access is retained.
- Use **🌐 → Artwork** for settings formerly shown as popup buttons. The
  existing Ctrl+wheel / Ctrl+- / Ctrl+= lyric zoom shortcuts still work.
- Saved appearance, geometry and configuration IDs remain unchanged. The
  remote tray uses the same renderer; restart an updated tray client to load it.

Verification: all 25 focused and related checks pass, including real Tk header
layout, long titles, border focus roundtrips, drag/resize handlers, the web
button URL, and browser hash scrolling. All 27 embedded modules compile and
match their editable sources; all eight generated web scripts pass syntax
checks. The final source was also run on the interactive Windows desktop:
foreground/background transitions kept the same HWND and 900×620 rectangle,
the header stayed mapped, and the focus border changed from gray to transparent
without callback errors. Windows styles contain no native caption/resize frame.
The screenshot tool timed out on both test windows, so final pixel-level visual
confirmation remains for the user.

After restarting V642, focus and unfocus the popup, resize it to a narrow width,
and click 🌐. Confirm that the bar stays visible, the inactive border disappears,
and the browser lands on Artwork. Playback was not stopped during development.

'''
p='docs/window-shortcuts.md';s=(ROOT/p).read_text(encoding='utf-8')
write(p,s+'\n'+section)
p='docs/README.md';s=(ROOT/p).read_text(encoding='utf-8')
s=s.replace('Current release: **V641** — consistent Emojimaxx solution colors in Web Karaoke and Floating Lyrics.',
            'Current release: **V642** — one-row artwork popup header, one web button, and an invisible inactive border.')
s=s.replace('- [Window shortcuts](window-shortcuts.md)',
            '- [Artwork popup header, borders, and window shortcuts](window-shortcuts.md#v642-artwork-popup-header-and-focus-border)')
s=s.replace('[Current V641 release notes](../releases/PAFPlayer_v641_emojimax_solution_color_parity_release_notes.md)',
            f'[Current V642 release notes](../releases/{name}_release_notes.md)')
write(p,s)
p='docs/windows-tray.md';s=(ROOT/p).read_text(encoding='utf-8')
s=s.replace('and the existing small emoji button in the artwork title bar stays in sync.',
            'and V642 keeps these choices in configuration rather than adding an emoji\nbutton to the artwork header. Its single 🌐 button opens Web Artwork settings.')
write(p,s)
p='docs/PAFPlayer_changelog.md';s=(ROOT/p).read_text(encoding='utf-8')
s=s.replace('# PAFPlayer changelog\n',f'''# PAFPlayer changelog

## V642 — November 4, 2026

Replace the artwork popup's two-row control area with one large song title and
one web button linking directly to Artwork configuration. Handle URL anchors
inside the web configuration scroller. Remove the native caption and frame that
overlapped the title and remained visible when unfocused. Keep the header visible
on focus loss while making only the border transparent. Preserve title dragging,
focused-edge resizing, window options, lyric zoom shortcuts and saved settings.
All 25 focused/related tests pass, as do 27-module bundle parity and web syntax
checks. Interactive focus transitions pass native geometry/style checks; desktop
screenshot capture timed out. [Release notes](../releases/{name}_release_notes.md).
''',1)
write(p,s)
notes=f'''# PAFPlayer V642 — artwork popup chrome

Released November 4, 2026.

## What changed

- One persistent header row: a large Artist - Song title beside one 🌐 button.
  Long titles ellipsize horizontally; no second row or overlapping caption.
- 🌐 opens the current player's `#artworkPopupSection`. The web scroller now
  resolves that anchor on initial load and when the URL fragment changes.
- The title/web-button bar stays visible when unfocused, as requested. The
  custom focus border becomes transparent; the native Windows caption, frame
  and shadow are removed permanently instead of clipping their outer two pixels.
- Drag the title to move; drag focused borders/corners to resize. Ctrl retains
  square resizing. Right-click the title for Always on top or Close; Alt+F4 works.
  Existing lyric zoom keys, taskbar access, settings and remote-tray behavior remain.

## Cause

The old implementation packed the title and buttons into separate rows while
retaining a normal native caption. Focus loss only changed the artwork wrapper
color; removing extended edge flags and clipping two outer pixels could not
remove the remaining native caption/frame. V642 uses a stable borderless Tk
window and a single custom header. Private, pointer-safe Windows API bindings
avoid interference with other popup callbacks, and the foreground query is
cached instead of rebuilding its binding on every focus poll.

## Verification

- **25/25 tests pass**, no skips: actual Tk layout and font sizing, long-title
  truncation, one-button URL, focus/geometry roundtrips, title dragging, minimum
  resize bounds, typed native APIs, URL-anchor navigation, and related existing
  artwork/floating-lyric geometry and solution-color tests.
- All **27 embedded modules compile and match their sources**; all **eight web
  scripts** pass Node syntax checks. Two historical border tests were updated
  to protect permanent border removal instead of the superseded pixel-clipping
  implementation; their debounce/non-reentrancy checks remain.
- Final source ran in an isolated popup on the interactive Windows account.
  Both focus states retained the same HWND and 900×620 position/size. The native
  style has no caption or thick frame. The header had exactly one label and one
  button, with non-overlapping bounds, and stayed visible on focus loss. Border
  colors changed gray → transparency key with **zero callback errors**.
- Screenshot capture failed with `window capture timed out: timed out waiting
  on channel` on both the popup and the normal test window; a direct button UI
  click also lacked coordinate geometry. The button callback was verified in a
  real Tk unit test, and hash scrolling in Node. Pixel-level visual confirmation
  and clicking through to a running player's web UI remain manual checks.
- No audio was started/stopped and no household-player commands or preferences
  were changed. All test fixtures and earlier failed attempts are retained.

[Test report](../tests/reports/v642-checks-20261104-084801.json) ·
[Interactive native trace](../tests/reports/v642-ui-20261104-084825.jsonl) ·
[Behavior and manual check](../docs/window-shortcuts.md#v642-artwork-popup-header-and-focus-border)

Restart PAFPlayer (and any tray-only computer using its own older copy) to load
V642. The currently running player is not hot-patched.

Source SHA-256: `{sha(source)}`.

## Files and root audit

The release Python file is a non-overwriting, hash-verified copy of the tested
active source. Documentation and changelog are updated; required backups were
verified as siblings before archiving. The complete path inventory is
`tests/reports/v642-change-manifest.json`.

The PAFPlayer, lockscreen and screensaver roots contain only active code,
required project inputs, or retained runtime/user sidecars. No obsolete files
needed moving and no files were deleted. **No literal C:\\BAT paths changed.**
`play_audio_file.py` was not modified.
'''
write('releases/'+name+'_release_notes.md',notes)
dest=ROOT/'releases'/(name+'.py')
with dest.open('xb') as f:f.write(source.read_bytes())
assert sha(dest)==sha(source)
print('RELEASE',dest,sha(dest))
