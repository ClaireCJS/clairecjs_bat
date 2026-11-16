# PAFPlayer `#` commands

During playback, press `#`, type one command, and press Enter. Use `#?` as a
short alias for `#commands` to get the command-list reminder. Commands are
case-insensitive and currently use letters and digits only; they do not take
arguments. `#volume` deliberately opens the existing interactive volume entry
mode, so the value is entered using the same editor as the `V` key.

| Command | Equivalent action |
| --- | --- |
| `#help` | Open the normal key-help overlay. |
| `#commands`, `#?` | Show a short reminder and point to this table. |
| `#dj` | Toggle AI DJ enabled/disabled. |
| `#djforce` | Force an AI DJ request now. |
| `#djwake`, `#wakedj` | Wake the AI DJ now, overriding its sleep schedule for this player session. |
| `#djsleep`, `#sleepdj`, `#sleeping`, `#bed`, `#bedtime`, `#sleepy`, `#sleep` | Put the AI DJ to sleep now and cancel pending/current DJ commentary for this player session. |
| `#quit`, `#exit` | Quit PAFPlayer. |
| `#play`, `#resume` | Play/resume. |
| `#pause` | Pause/resume. |
| `#stop` | Stop playback. |
| `#next` | Next track. |
| `#previous`, `#prev` | Previous track. |
| `#nextfolder` | Next folder. |
| `#previousfolder`, `#prevfolder` | Previous folder. |
| `#volume`, `#vol` | Enter direct volume mode, like `V`. |
| `#volup`, `#voldown` | Change volume by 5%. |
| `#volup20`, `#voldown20` | Change volume by 20%. |
| `#volreset` | Set volume to 100%. |
| `#reset` | Reset volume and playback speed. |
| `#speedup`, `#speeddown`, `#speedreset` | Change or reset playback speed. |
| `#repeat`, `#repeatnext` | Cycle repeat mode forward. |
| `#repeatprevious` | Cycle repeat mode backward. |
| `#repeatdouble` | Jump repeat mode by two. |
| `#shuffle`, `#shufflenext` | Cycle shuffle mode forward. |
| `#shuffleprevious` | Cycle shuffle mode backward. |
| `#shuffledouble` | Jump shuffle mode by two. |
| `#randomize` | Randomize the playlist. |
| `#loop` | Toggle looping. |
| `#playlist` | Toggle the playlist window. |
| `#warnings` | Open the currently applicable warning history. |
| `#urls` | Browse available URLs. |
| `#url` | Open the primary URL. |
| `#visualizernext`, `#visualizerprevious` | Change visualizer mode. |
| `#karaokenext`, `#karaokeprevious` | Change karaoke style. |
| `#treatmentnext`, `#treatmentprevious` | Change karaoke treatment. |
| `#emoji` | Toggle karaoke emoji treatment. |
| `#artwork` | Toggle the external album-art window. |
| `#floatinglyrics` | Toggle floating lyrics. |
| `#sixel` | Toggle the SIXEL visualizer. |
| `#fps` | Toggle the FPS HUD. |

Unknown commands remain harmless: PAFPlayer shows an “Unknown command” notice
and continues playback. The web AI DJ **Talk Now!**, **Wake now**, and **Sleep
now** buttons send the same `#djforce`, `#djwake`, and `#djsleep` actions through
the player’s authenticated workflow endpoint. Manual wake/sleep lasts until the
opposite command or a player restart; it does not rewrite the saved schedule.
