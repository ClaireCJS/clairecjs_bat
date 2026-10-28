# Web configuration notes

## V618 playback device default

In the Playback tab, the **Device:** chooser keeps **Fav** and **Def** beside
the chooser. Click **Def** to confirm and save the selected output-device
combination as the persistent default. The Playback tab mirrors the underlying
controls; its Def click now reaches the same saved-default action as the
original control, and the selected mark remains visible after saving. It does
not change the current output until the device selection itself is changed.
The two copies use separate radio groups, so both can show the saved default.

## V589 bass and shuffle controls

The Playback tab shows a numeric percentage box immediately to the right of
each bass slider. Moving a slider fills its box; typing an integer in the box
sets the same control and saves through the existing bass setting. The locked
control reads **Reduce bass by X% while locked**. The signed boost/reduction
control reads **Reduce bass by X%** for negative values, **Boost bass by X%**
for positive values, and **No bass change (0%)** at zero. A `%` unit appears
beside each box. Locked reduction remains unavailable until its checkbox is
enabled.

**Fresh shuffle after** keeps the value and **hours** on one line. It is greyed
out for Sequential, Shuffle randomly, folder/playlist repeat, and Repeat OFF,
because the saved shuffle age governs only **Shuffle by history**. Its saved
value is preserved when switching modes.

## V577 custom frequency spread

Experimental **Configure custom…** now describes the frequency curve in terms
of two axes: horizontal display position and vertical source-frequency
percentile. Each slider is labeled **At display 20/40/60/80%** and shows the
source percentile placed there. A live explanation says how the first point
spreads or compresses low frequencies. The curve remains monotonic. Named
profiles can be saved, loaded, and deleted in the same existing web-preference
storage; loading a profile updates the editor, and **Apply custom spread** sends
the four points to the player. Existing saved mode IDs and profile data remain
unchanged.

## V576 progress color layers and experimental console title

The Progress Bar section has **Invert order** and **Invert palette** checkboxes.
Invert order reverses the position sampled along a color gradient; invert palette
complements each RGB color. Both are independent of the existing progress color
mode, whose saved numeric IDs remain unchanged. **Beat color overlay** selects
one of the existing color modes, or None. On a detected beat, it blends that
mode's per-cell gradient over the base mode. For example, select Rainbow for
the base and American Flag for the beat overlay. Beat detection and the beat
treatment still control timing; the overlay does not affect audio.

Experimental includes 25 large rainbow **PAFPLAYER** title designs, made from
five lettering treatments and five color sweeps. The title occupies about half
the terminal and uses the existing 2×4 DRCS art glyph bank. It appears for five
seconds on the first track of a run. **Test title for 5 seconds** redraws it
without stopping playback. The custom title dropdown keeps it on the console
while open and for ten seconds after closing. Choosing a title saves its style
for future runs. Terminals without usable DRCS support may show fallback glyphs.

## V572 Last.fm tab

The web configuration now has a dedicated **Last.fm** tab beside **Metadata / Maintenance**. It contains **View my Last.fm profile** and **Force Last.fm scrobble**; those actions no longer appear among general metadata controls. The profile action uses the saved username and, if none exists, asks for it on the player computer. Last.fm credentials for scrobbling remain configured on the player computer. A remote browser can view the profile, but changing the username remains local-only.

The tab uses PAFPlayer's existing action queue and profile API. It does not create a second scrobble path or alter the normal scrobble eligibility rules.

## V540 playback-device choices, artwork blend, and automatic height

The Playback **Device:** chooser now has **Fav** and **Def** controls. A mark
stores the exact selected output combination, including simultaneous outputs,
rather than only the first endpoint. The Visualizer **Bar artwork blend** chooser
also supports favorite and default modes, and its selected mode now persists.

**Auto-set to tallest** now passes web-action validation, saves immediately, and
updates the visualizer height when enabled and whenever console geometry changes.

## V536 progress reactivity and visualizer height

Adaptive Loudness progress-bar detection now uses the current file-playback
spectrum whenever it is available, with the precomputed timeline retained only
as a fallback. The Color-intensity throb treatment draws a bright playhead edge
whose illumination decays backward through the filled bar, making both the flash
and its falloff visible instead of assigning one flat color to every filled cell.

Artwork Seaming now accepts its full 0-based range in the Fav and Def controls,
including strategy 0.

The Visualizer Rows control labels its one-shot geometry action **Set to tallest**.
The adjacent persistent **Auto-set to tallest** checkbox recalculates the tallest
usable row count whenever terminal or HUD geometry changes. Turning it off keeps
the most recently selected row count.

## V535 saved shuffle lifetime

The Playback section includes **Fresh shuffle after**, measured in hours. It
controls how old a persistent playlist shuffle may be before PAFPlayer rebuilds
it from current listening history. Values range from 0 through 168 hours in
quarter-hour steps. Zero always rebuilds. V535 originally used five hours;
**the current factory default is 72 hours** (V584). Saved choices remain in
effect. Changes save immediately and apply to subsequent playlist cache
decisions in Shuffle by history mode.

## V502 playback progress lyric preview

Hover over the playback progress bar to see the time and the lyric that Web Karaoke would display at that seek position. The preview follows the same lyric timeline and karaoke offset as the live display, including tracks with a trimmed playback start. When the timeline is blank, the most recent lyric appears at 50% opacity for five seconds after it disappears; after that the preview says no lyric is available. Clicking the bar still seeks to the hovered position. The tooltip is separate from the bar so it stays visible instead of being clipped.

## V496 three Web Config Emojimaxx rows

Web Karaoke, Artwork Pop-Up, and Floating Lyrics each display their Emojimaxx controls on a separate row in their own section. Artwork and Floating Lyrics Web Config rows now expose their independently saved solution visibility, size, distance, over/under placement, inherit lyric colors, color, and opacity settings. Edits go through the player action queue to the appropriate Tk lyric window and persist across launches. The existing native configurator controls remain available.

## V494 Web Lyrics solution controls

The Web Karaoke section has its own **Show Emojimaxx solutions** checkbox and sliders for solution size (5–150% of lyric size), signed vertical distance (-50% to +50% of the main lyric font size, default 1%), and opacity (0–100%, default 100%). Positive distance moves the answer farther away on the selected side; negative distance pulls it toward or across the lyric. **Over** moves the answer above its emoji; under is the default. Choose a solution color, or enable **Inherit lyric colors** to hide the picker and follow the token's current lyric color. These settings are saved separately from Floating Lyrics and Artwork Lyrics. The controls appear when Web Emojimaxx is enabled.

The Artwork EmojiMaxx config shortcut focuses its Artwork solution row.
