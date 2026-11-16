# Web visualizer

## V637 lyric bounds correction

When **Auto-Expand Lyric Size** is on, the chosen font must keep the rendered
characters inside the lyric panel, including characters that extend beyond the
browser's reported line-box height. This matters most for very large text in a
wide browser window. The panel-height handle still sets the available space.
Its saved manual height now takes priority when the handle is dragged smaller,
and the font is refitted as the panel changes size.

Clicking the web progress bar updates the displayed position immediately. The
player then confirms the seek, and the page reconciles to its playback clock.
The audio seek still depends on decoder startup and the running player's event
loop; this display change does not promise zero audio latency.

Timed lyrics stop occupying the console and taskbar title after 15 seconds,
including when the next cue is much later or a sidecar supplies an unusually
long end time. The browser lyric title timeline follows the same cue limit.

The **Silence / overlap between tracks** control has an editable seconds box
to the right of its slider. Enter a value from -5 to +5 seconds. Positive
values add a pause between tracks. Negative values are stored as overlap
requests; actual overlapping playback is not yet supported by the renderer.
The Web configuration tab strip follows the same order as its sections when
scrolling.

## V636 Web Karaoke lyric fitting

**Auto-Expand Lyric Size** fits each current lyric to the lyric panel's actual
width and height. Short cues grow to fill the assigned space; long or wrapped
cues shrink when needed so their text stays in the panel. Drag the handle
below the lyric panel to assign more or less height. The fitting is local to
the web page and does not change the console or floating lyric font settings.

The V636 fix removed an incorrect horizontal margin from the browser's
`scrollWidth` comparison. Because that width already includes the whole lyric
element, the old comparison rejected every normally fitting line. The fitter
now searches in both directions and allows long words to wrap. It keeps a
small edge margin so glyphs do not touch the clipped panel boundary.

The web visualizer has a **Web visualizer** checkbox in its toolbar. Turning
it off leaves the surrounding player controls and configuration available but
stops the web visualizer frames and hides the canvas.

The visualizer canvas can also be double-clicked to toggle it on or off. The
checkbox and double-click action use the same saved web-visualizer state and
stay synchronized with the player.

Web-page initialization is read-only for artwork coloring/autoslide settings.
Those settings are sent to PAFPlayer only when the user changes the related
controls, so opening or closing the webpage does not trigger console visualizer
announcements such as the art/black colorslide message.

## Beat-reactive progress timing

V538 displays the **Beat visual timing correction** value in an editable
millisecond box to the right of its slider. The slider snaps to `0` throughout
the ±15 ms center zone; the box accepts any whole-millisecond value from -250
through +500. The factory/default value is `0 ms`.

Progress-bar beat energy is selected by the same canonical millisecond source
timestamp used by lyrics, the spectrum, and the progress position. The live
spectrum is used only while the matching timestamped analyzer sample is not yet
available, preventing render-loop timing from becoming the long-term beat clock.
## V588 web visualizer labels

The visualizer header shows its on/off checkbox without the extra “Live
spectrum” caption. The output-format status chip uses the compact “Out:” label;
its sample rate, bit depth, and optional source bitrate remain available.

