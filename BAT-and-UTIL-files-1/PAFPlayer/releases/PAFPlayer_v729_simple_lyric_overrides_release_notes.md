# PAFPlayer V729 — simple lyric preview

## Changes

- Added `--use_lrc FILE`, `--use_srt FILE`, and `--use_txt FILE`.
- An explicit lyric file is used for the first dispatched audio item only.
- `--simple` now behaves as an inline player: it preserves console history,
  avoids screen clearing, and leaves the console title unchanged.
- Normal playback and normal lyric discovery remain unchanged.

## Example

```text
PAFPlayer.py --simple --use_lrc C:\preview\song.lrc C:\music\song.mp3
```
