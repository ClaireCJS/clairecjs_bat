# Floating Lyrics positioning

## V605 whole-window opacity

Web Configuration → Floating Lyrics now has a **Floating lyrics opacity** slider
from 10% to 100%. It changes the whole lyric window immediately and saves the
choice as the default for future runs. The factory default remains 100% when no
setting exists. The edit border and title strip temporarily display at full
opacity while the window is being moved or configured; the chosen opacity
returns when edit mode ends. The slider affects the lyric window, not the
separate Emojimaxx answer-opacity control.

`--floating-lyrics-opacity=45` applies 45% for the current run without changing
the saved default. When an official PAFPlayer instance is already running, the
option is handed to that instance through its authenticated local IPC; it also
works alongside a media filename. `--default-floating-lyrics-opacity=75` saves
75% as the default in the existing global FloatingLyrics settings branch.
Both options also accept a space before the number. Values must be whole
percentages from 10 through 100. If both are used, the session value controls
this run and the saved default controls later runs. A default-only command
saves and exits without starting playback.

## V574 remote stability and Whip glyphs

Remote tray clients retain sung lines instead of repeatedly restarting the track
intro. Visibility changes apply once, including restored-enabled startup; old
intro timers are canceled and Tk controls use their owning interpreter. Whip
Emojimaxx uses Segoe UI Historic when the selected font lacks its hieroglyphs.
See [the diagnosis, tests, custom HTTP port and remote verification guide](remote-floating-lyrics-v574.md).

## V573 legacy lyric character recovery

Floating Lyrics now renders text containing a leaked Windows-1252 control character such as U+0089 as its printable symbol, `‰`. Other defined Windows-1252 characters in the same range, including curly quotes and dashes, are recovered the same way. The repair applies to sidecar files, embedded lyric tags, and direct lyric updates; the floating bitmap also checks its input before drawing. Raw lyric files are not rewritten. Invalid UTF-8 sidecars are read as Windows-1252 rather than displaying replacement characters.

## V540 Web Config shortcut

The Floating Lyrics title bar uses a compact **🌐** button in place of the old
**EMX cfg** caption. Its tooltip identifies it as a link to the PAFPlayer web
interface, and clicking it opens the Floating Lyrics / Emojimaxx configuration
section in the browser.

## V496 floating lyric rendering fix

An Emojimaxx answer triggered a `NameError` while creating its translucent image, preventing the entire floating cue from finishing. Solution images now use the owning Tk root. Answer drawing is isolated so a future answer error leaves the primary lyric visible.

## V494 independent Emojimaxx solution controls

Floating Lyrics and Artwork Lyrics each have their own **Show Emojimaxx solutions** controls in their lyric coloring configurator. Each set saves its own size (5–150% of the main lyric), signed vertical distance (-50% to +50% of the main lyric font size, default 1%), and over/under placement (under by default). Positive distance moves the answer farther away on the selected side; negative distance pulls it toward or across the lyric. A color picker and opacity slider (default 100%) set the answer appearance. **Inherit lyric colors** hides the picker and follows the current lyric color, including animated colors. Solutions are rendered with alpha-capable images so opacity also works in the desktop windows.

V529 applies a subtle rightward optical correction equal to 2% of the primary
lyric font size. The correction is shared by Web Karaoke, Floating Lyrics, and
Artwork Lyrics; it does not change the saved vertical-distance setting.

The floating renderer now splits mixed emoji runs when the preferred font lacks individual glyphs, using Segoe UI Symbol for supported fallback characters while keeping joined emoji sequences together.

## V492 floating glyphs and teeny answers

When no Floating Lyrics teeny preference has been saved, answers now start enabled; an explicit off selection remains off. Floating lyric lines now check the selected font for each emoji or symbol run and use Segoe UI Symbol when Segoe UI Emoji lacks the glyph. This covers substitutions such as 🞨 and 🠈 while keeping color emoji in their normal font. Teeny answers use the same mixed-font widths and fitted line position as the lyric bitmap, so labels sit beneath their substitution even when emoji and text fonts differ. The optional answer size and enable settings remain separate from Web Karaoke.

## Teeny Emojimaxx solutions

PAFPlayer V490 can display the textual solution for an Emojimaxx substitution directly beneath its emoji in Floating Lyrics, matching Web Karaoke's experimental teeny-solutions feature. Enable **Teeny answers** from the floating window's edit title bar, its context menu, or **Show teeny Emojimaxx solutions** in the Floating Lyrics configurator.

The configurator provides an independent **Size** control from 5–150%, with a default of 20% of the primary lyric font. The enable state and size are stored separately for Floating Lyrics and survive restarts. Extra line spacing is reserved while the feature is active so answers do not collide with the following lyric line. Existing pointer-hover solution tooltips remain available whether or not teeny answers are visible.

Visible answers require Floating Lyrics Emojimaxx to be enabled and a substitution with solution metadata to be present. Turning the feature off does not alter lyric text or Emojimaxx settings.

The Floating Lyrics **Bring to Center** and **Center Over Visualizer** actions
temporarily use the editable window state while repositioning the window, then
restore the normal transparent, borderless lyric state after the move. The
button-driven move is tracked separately from mouse dragging so a focused
button action does not leave a flashing visible edit border around the lyrics.

Mouse-driven movement and intentional focus/edit interactions retain their
existing visible editing chrome.

## V486 transition scheduling

New cues cancel the previous color-animation timer before rendering. A full
animation interval follows the initial upload, avoiding an immediately due recolor.
Text fonts are cached by pixel size (256 entries); duplicate measurements within
an autosize candidate are reused. Typography and bitmap output remain unchanged.
See [performance validation and limitations](performance-v486.md).
