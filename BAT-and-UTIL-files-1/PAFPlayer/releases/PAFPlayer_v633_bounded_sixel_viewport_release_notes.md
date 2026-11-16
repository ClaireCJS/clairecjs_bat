# PAFPlayer V633 — bounded SIXEL viewport

The optional console SIXEL visualizer could leave repeated HUD and lyric frames
in Windows Terminal scrollback. PAFPlayer converted the requested terminal rows
to Chafa `--view-size` as though that option used 8-by-8 pixels; Chafa actually
uses terminal columns and rows. An eight-row reservation could therefore produce
a much taller image. Chafa also appended CR/LF after the image, advancing the
cursor again.

V633 chooses a view size from the reserved pixel budget, checks the raster
dimensions in Chafa's output, retries smaller dimensions when necessary, and
removes the trailing newline before painting. The moving SIXEL visualizer and
static cover layer share this guard. The cover layer now requests Chafa's
supported 256-color mode.

`PAFPlayer resume --theory=7` and `PAFPlayer --resume --theory=7` now accept
the saved-session command with following options. The no-option `resume` and
`--resume` forms continue to work.

Focused tests verify both SIXEL paths, Chafa raster bounds at normal and small
font sizes, newline removal, and both resume spellings. A live Windows Terminal
restart with SIXEL enabled is still needed to verify the reported scene. Font
geometry reported by Windows may differ from Windows Terminal's actual zoomed
cell size; if so, further calibration may be needed. V633 does not alter audio
playback, saved visualizer preferences, or the running V632 process.
