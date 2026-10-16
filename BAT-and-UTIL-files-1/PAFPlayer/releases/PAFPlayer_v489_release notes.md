# PAFPlayer V489 — Volume keys and bass-lock persistence

- Both lowercase `v` and capital `V` open direct volume entry.
- `M` and `Shift+M` now select the next and previous visualizer modes.
- `Bass Reduction while Locked` immediately republishes its persisted state to the web UI, preventing a stale status poll from clearing the checkbox.
- The dependent bass-reduction slider is synchronized after checkbox restoration.
