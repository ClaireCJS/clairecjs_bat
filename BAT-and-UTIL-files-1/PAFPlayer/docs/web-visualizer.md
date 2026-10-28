# Web visualizer

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

