# PAFPlayer V589 — web bass and shuffle controls

Released October 20, 2026.

The Playback tab places an editable percentage box immediately beside each bass
slider. Slider movement updates its box, and a typed percentage updates the
slider through the existing setting. The labels summarize the effect as bass
reduction, boost, or no change. The saved setting IDs and ranges are unchanged.

“Fresh shuffle after” keeps “hours” beside the numeric value. The control is
greyed out except in Shuffle by history, since only that mode uses the saved
history shuffle age. Changing modes does not erase the saved value.

Validation: the existing bass tests passed, Python source parsed, the rendered
web script passed `node --check`, and generated labels and schema were checked.
The web layout has not been visually checked in a live Windows browser.

V588's web visualizer labels, V587's continuous F2 rename, and V586's install
survey rehearsal remain included.
