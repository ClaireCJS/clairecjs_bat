# V482: song-specific scrolling investigation

## V635: periodic visualizer stalls and resume checkpoints

During a live V634 run with SIXEL disabled, `/api/status` reported roughly
36–54 painted frames per second against a requested 73–120, with full-frame
terminal transport taking about 3–8 ms per write. This establishes that the
regular DRCS spectrum and Windows Terminal transport need separate attention
from the earlier SIXEL scrollback defect. The reported one-second hitch was
not measured frame by frame, so its exact source is not proven.

The high-rate `show_status()` callback also synchronously saved playlist
resume state every two seconds. Each save computed the playlist successor and
wrote two Registry values before the next visualizer frame could begin. V635
queues those periodic checkpoints to one worker; pending positions coalesce
to the latest one. The first bookmark is still established before decoder
startup, and a track handoff waits for the previous track's queued write
before clearing or replacing its bookmark. Normal process exit gives the
worker a bounded drain period. An abrupt process kill can still lose the most
recent unsaved position.

Frame buffering would add visual latency and would not increase the terminal's
capacity. Moving the whole renderer to another process would still require
terminal transport and synchronization with playback state. The next useful
measurement is a short-window breakdown of generation, Registry/other main
loop work, and terminal write latency while the visible hitch occurs; the
five-second `/api/status` `visualizer_perf` counter is too coarse to identify
an individual one-second pause.

## V634: SIXEL enable confirmation and startup warning

The optional SIXEL checkbox in web configuration requires two separate
confirmations when turning it on. Cancelling either leaves it off. Turning it
off needs no confirmation. A newly started playback instance prints a warning
when SIXEL is active, whether enabled by the saved `SixelEnabled` preference
or by a command-line option. It suggests `--no-sixel-visualizer` for a
session-only escape. An already-running player cannot display a startup
warning retroactively.

The V633 bounded SIXEL change was checked in the live Windows Terminal with
SIXEL enabled; the user confirmed that HUD frames stayed in place.

## V633: bounded SIXEL output

The V632 live screenshot showed whole HUD frames stacking while playback and
the current spectrum continued. The active status also showed the optional
SIXEL visualizer enabled. Chafa documents `--view-size` in terminal columns
and rows. PAFPlayer had treated those values as 8-by-8 pixel units, so its
requested raster could be much taller than the eight rows reserved for SIXEL.
In a local Chafa probe, an 8-row request using the old conversion produced a
15-row image. Chafa also appended CR/LF after the image, moving the cursor.

V633 sizes Chafa output against the actual cell-pixel budget, checks the
declared SIXEL raster dimensions before writing it, retries smaller geometry
when needed, and sends only the image sequence without Chafa's trailing
newline. Both the moving SIXEL spectrum and the static cover layer use this
path. The cover layer now uses a supported Chafa color count. Focused tests
check several cell sizes, including a small zoomed font. A live Windows
Terminal run confirmed that the repeated HUD blocks stopped accumulating.

## V632 follow-up: bottom-edge scroll protection

The same accumulating-frame symptom was reported with V628 and V631. Both
versions allowed the spectrum to paint the terminal's final physical row. V632
reserves two rows below the UI and uses an absolute viewport address for every
full spectrum repaint. This prevents a prompt, HUD paint, or terminal cursor
change from making a subsequent frame navigate relative to the wrong row. The
diagnostic theory 14 relative re-home is retired; it remains accepted for old
commands but uses absolute addressing. The safety margin makes the spectrum at
most two rows shorter. Source-level and renderer tests cover the row bound and
frame-origin rule. Live Windows Terminal reproduction remains the final check.

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
