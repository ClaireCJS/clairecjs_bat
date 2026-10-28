# V482: song-specific scrolling investigation

## V484 Ctrl+Break cleanup contract

Ctrl+Break is an immediate abort path. Before any child/window/server cleanup,
PAFPlayer writes terminal controls directly to the console: reset attributes,
select normal-size DEC line rendition, restore autowrap and cursor visibility,
then home and erase from the cursor through the end of the screen. The final
process-exit path does not wait for ordinary workflow/server shutdown joins;
Windows releases those process-owned resources at exit. This behavior also
applies if Windows Terminal reports Ctrl+Break as `SIGINT`.

Reported symptom: certain songs turn the fixed console HUD/visualizer into
rapidly accumulating scrollback. The supplied capture contains 1,221 copied
lines, but no original ANSI commands. It identifies Dethklok's **Murdertrain A
Comin' (TV Edit)**, around 28–44 seconds.

The trace log resolved the exact source to:

```text
T:\new\MUSIC\changerrecent\Metalocalypse\MISC\Murdertrain A Comin' (TV Edit) [from S1E14_Bluesklok].mp3
```

## Confirmed issues and changes

- Visualizer frames restore DECAWM (automatic wrapping), but HUD/lyric paints
  previously relied on the no-wrap state set at track startup. Fixed-row cursor
  positioning now explicitly reasserts no-wrap before every anchored paint.
  Shutdown still restores ordinary wrapping. This is a defensive correction
  for terminals supporting DECAWM, not proof of the complete reported cause.
- The exact track contains an invalid embedded APIC image beginning with
  `10 4A 46 49 46` rather than a valid JPEG header. Its matching 1400×1400 JPEG
  sidecar is healthy. The artwork-variant collector previously retained both,
  causing repeated popup decode/crossfade errors. With Pillow available, failed
  decodes are now excluded before entering the artwork rotation; the healthy
  sidecar remains. Without Pillow, the existing Chafa fallback is preserved.
- This change does not repair or overwrite the MP3 or its embedded tags. A
  before/after SHA-256 check confirmed that the reproduction MP3 was unchanged.

## What was tested

- Eight focused regression tests cover row-prefix wrapping state, cleanup,
  corrupt-art fallback, Windows metadata/lyrics, lyric timing, artwork-cache
  reuse and the web checkbox.
- A renderer-only harness initializes the actual nested PAFPlayer rendering
  functions using the exact track's real lyrics and metadata. It does not start
  audio, worker threads, history writes or settings writes. The spectrum is
  synthetic. A hidden private Windows console replayed 240 frames from 25–33
  seconds, including the gap/re-entry shown in the capture, with **zero viewport
  movement** at 120×30.
- This is not an end-to-end Windows Terminal reproduction with live artwork,
  audio and all background workers. The original runaway-scrolling failure is
  therefore **not yet conclusively reproduced or verified fixed**.
- A deliberately over-wide test showed that the installed legacy Windows 10
  console host does not prevent scrolling with DECAWM or the attempted native
  mode guard in its VT path. The ineffective native guard was removed; no
  per-frame console-mode syscalls were retained. The diagnostic is available as
  `--native-console 3 --fixed` in the V482 test script, but is not a passing
  regression assertion or a guarantee for legacy conhost.

## Next real-session check

Restart into V482 and replay the exact TV edit, especially the 25–33 second
transition. If scrolling persists, retain terminal dimensions, Windows Terminal
version, renderer/transport and artwork settings, plus the relevant trace/error
log interval. A raw VT capture would distinguish cursor-state corruption from
text wrapping; a plain copied-console transcript cannot preserve that evidence.
Do not change preferences, reduce frame rate, or rewrite music tags merely to
hide the symptom.
