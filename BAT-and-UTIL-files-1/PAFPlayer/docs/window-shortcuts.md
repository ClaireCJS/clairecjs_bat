# Artwork and Floating Lyrics window shortcuts

- `Ctrl+Alt+A` brings the external artwork window to the foreground. The web
  Artwork `Bring to Top` button shows this shortcut in its tooltip.
- There is currently no dedicated keyboard shortcut for bringing Floating
  Lyrics to the foreground. `Ctrl+Alt+F` is already assigned to the five-second
  visualizer performance HUD, so it is not an equivalent Floating Lyrics key.

## V645 resize cursors and focus-only maximize

While the Artwork Pop-Up is focused, its borders show the standard Windows
horizontal, vertical, and diagonal resize cursors. Each cursor matches the
edge/corner used for dragging. Moving back into the content, leaving the window,
or switching focus clears the resize cursor.

A **□ Maximize / ❐ Restore** button appears over the right end of the song title
while focused. It may cover part of the title, but does not shrink the title row
or move the artwork/lyrics. The web button remains beside it. On focus loss the
maximize button and outer border disappear; the title and web button remain.

Maximize fills the current monitor's Windows work area. Restore returns to the
previous normal rectangle, including negative coordinates on secondary monitors.
If that monitor is disconnected, Restore clamps the normal window to an available
monitor. The popup stays borderless throughout; no native frame is reintroduced.
While maximized, restore first to drag or resize the window. Idle gallery motion
and automatic artwork compaction cannot move/shrink the maximized popup. Monitor
or taskbar layout changes refresh its work area. Saving/closing while maximized
preserves the normal rectangle, so restart opens at the normal size.

After restarting V645, focus the artwork window and hover all four edges and
corners. Confirm the pointer directions, click □, switch focus away/back, then
click ❐ and confirm the previous rectangle returns. Repeat on a second monitor
if used. Remote tray computers need their own updated copy and restart.

Verification: 44 focused/related tests pass, including actual Tk cursor names,
focus-only visibility without reflow, mocked multi-monitor/failure cases, saved
normal geometry, and a real Windows SetWindowPos maximize/restore roundtrip with
the same borderless HWND. V643 karaoke fitting and V642 border/header regressions
remain covered. The isolated interactive popup also recorded both focus states,
matching button visibility and unchanged HWND/geometry with no callback errors.
Desktop screenshot capture failed (`FrameArrived timed out`), so final visual
inspection of the pointer shapes and clicking the button remain manual.

## V643 artwork karaoke fills the window

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

## V642 artwork popup header and focus border

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

