# 🎧 PAFPlayer / `play_audio_file.py`

PAFPlayer is a Windows-first, keyboard-driven terminal media player built around FFplay, FFmpeg, and FFprobe. It combines dense width-aware metadata, playlist/history logic, Last.fm, timed karaoke and EmojiMaxx, terminal and browser visualizers, local/web control, album-art discovery, a persistent external art window, and deliberately exact terminal geometry.

## V180 — dual lyric destinations + independent lettering profiles

V180 restores simultaneous GUI lyrics. The artwork-window **Lyrics** control is again a three-way cycle, now deliberately **Over Artwork → Floating → Both**. `Both` keeps the same current cue visible over the cover and in the independent transparent floating-lyrics window at the same time. The old pre-V180 persisted `Off / Artwork / Floating` value is migrated once into the new `Artwork / Floating / Both` setting; there is no new Off position in this three-way control.

The artwork control strip no longer uses a coloring-name selector. A **🔡** button appears only when over-art lyrics are enabled and opens the artwork-lettering configurator; a separate **🔠** button appears only when floating lyrics are enabled and opens the same configurator UI for a completely independent floating-lyrics profile. In `Both` mode both buttons are visible. The two destinations share the same 15 rendering treatments and palette catalog but persist their **Enabled**, **Default**, **Favorite**, per-style **Palette**, per-style **Speed**, and per-style **Timed emphasis** values separately.

Each configurator style row now puts **Enabled**, **Default**, and **Favorite** together. Enabled is an exclusive radio choice and changes the live style for that destination; Default is a separate exclusive radio choice; Favorite remains multi-select. The old TV/Show selector is gone, and the large hero preview always demonstrates the currently Enabled style. Palette controls are readonly comboboxes whose **Up/Down arrows cycle palettes immediately while the control retains focus**, making rapid visual comparison possible without repeatedly reopening the dropdown. Every style also has a persistent 0.25×–4.00× animation-speed slider.

**Timed emphasis** adds a MiniLyrics-like sung-progress sweep to any lettering treatment. PAFPlayer computes 0–1 progress through the active cue from its explicit end timestamp, the following cue start, or the normal untimed-line duration. The already-sung side of the text receives a moving palette highlight with a soft frontier that travels left-to-right as the line plays. The same mechanism is used independently by over-art and floating lyrics, including Solid and Rainbow-letter modes as well as the patterned treatments.

Opening either lettering configurator still reserves PAFPlayer's visual-animation budget for the configurator: console/web visualizers and live artwork/floating lyric animation freeze while audio and lyric timing continue. The newest cue and emphasis progress are retained internally and both enabled lyric destinations catch up immediately when the configurator closes.

Regression coverage verifies the three destination states, independent artwork/floating persistence keys, conditional 🔡/🔠 buttons, Enabled/Default/Favorite semantics, keyboard palette cycling, speed sliders, timed-emphasis progress, and emphasis publication from playback into both GUI lyric renderers.

## V179 — opportunistic Album/URL colon alignment

V179 tightens the information-first HUD optimizer using the supplied Black Dresses / Cats Millionaire example. The previous optimizer correctly preserved all metadata but missed an obvious cheap relationship: `Album:` and `URL:` could share the same colon column by spending only three otherwise-unused cells.

The main V169 optimizer still chooses the complete two-row layout first. V179 then runs a deliberately small **cross-lane beauty pass**. For `Album:` / `URL:`, if the two labels are on different rows and their colons differ by at most 12 cells, the earlier field and every field after it on that row may slide right by the required amount **only if the entire row suffix still fits**. Nothing is truncated, dropped, reordered, or moved left. If the shift would overflow—or would require a large wasteful padding jump—the original dense layout is kept.

This preserves the intended priority order: information density first, then alignment when alignment is genuinely cheap. The supplied Black Dresses case is now a regression test, along with negative tests proving that the beauty pass refuses both overflow-producing shifts and excessive padding. No playback, visualizer, artwork, web, karaoke, hotkey, or lettering-configurator behavior changes in V179.

## V178 — clipped adaptive coloring previews + single artwork border

V178 fixes the maximized lettering-configurator corruption shown in the supplied screenshot. The embedded style table no longer forces its internal window to the viewport height; every style row keeps its natural requested height and each preview remains clipped to its own Canvas. Row previews are deliberately smaller now that the large hero/marquee exists. Pattern-mode text masks are cached by mode and canvas geometry, and the existing Canvas image item is updated in place rather than being destroyed and rebuilt for every frame.

The hero/marquee and row samples now have **independent animation clocks**. The hero remains fixed at **20 fps (50 ms)** whenever the configurator is visible. The secondary row previews are staggered in a round-robin over only the rows currently visible in the scroll viewport. Their render cost is measured with a moving average; if row work is consuming too much of its budget, the row scheduler automatically backs off as far as 650 ms, then gradually recovers toward its normal 110 ms cadence when headroom returns. Row load therefore cannot deliberately reduce the hero speed.

The apparent double 5px album-art border is also corrected. The Tk Canvas highlight already owns the single monitor-scaled focus border; the normal Pillow artwork renderer had additionally subtracted `border * 2` from the image's drawable width and height, creating a second transparent 5px gutter immediately inside the real border. V178 renders artwork against the Canvas drawable extent exactly once. The focus border remains visible only when the artwork popup is focused; the existing Windows native-edge suppression remains separate.

Regression coverage verifies intrinsic non-overlapping row geometry, independent hero/row schedulers, adaptive row-preview backoff/recovery, cached pattern layouts and in-place image updates, and the single-border/no-inner-gutter rendering rule.

## V177 — exclusive coloring-config animation budget, per-style palettes, and 15 lettering modes

V177 gives the artwork-letter-coloring configurator exclusive use of PAFPlayer's visual-animation budget while it is open. Audio playback continues normally, but the terminal DRCS/SIXEL spectrum, the browser spectrum and browser karaoke animation, modal-prompt visualizer pumping, background spectrum-analyzer chunk launches, and the album-art over-art karaoke animation all pause/freeze. Closing the configurator releases the pause immediately: the console/web visualizers resume, the newest lyric cue is applied to the artwork popup, and the selected artwork lettering animation resumes. This is specifically intended to keep the configurator's hero and visible live samples smooth instead of making every renderer compete at once.

The browser's compact `/api/spectrum` payload now carries a visualizer-pause state. While paused, the browser leaves the existing spectrum frame untouched rather than clearing it, and its rainbow karaoke animation also freezes. The terminal behaves similarly: status/time can continue updating, but spectrum painting is skipped. The analyzer worker also waits before launching another FFmpeg spectrum chunk while the configurator is active.

The configurator itself now spends work only on rows that actually intersect the scroll viewport. The large hero preview still animates every configurator tick; visible row samples animate together, while off-screen rows consume no ImageTk rendering work and update as soon as they are scrolled into view. A small round-robin fallback remains for geometry states where visibility cannot yet be measured.

Every lettering type now has its own **Palette** dropdown using the existing PAFPlayer palette catalog. Palette choices are independent per lettering mode and persist together in the normal `Software\ClaireCJS\play_audio_file` settings cache under `ExternalAlbumArtKaraokeColorPalettes`. Favorite and Default behavior remains independent of palette selection.

V177 expands the coloring catalog from 3 modes to **15**. The original Plasma, Rainbow letters, and Solid behavior remain as the first three entries (Solid is now palette-colored), plus twelve new animated treatments: **Horizontal wave, Vertical wave, Diagonal wave, Radial ripple, Vortex, Checker pulse, Neon stripes, Lava lamp, Aurora curtain, Electric zigzag, Sparkle field, and Kaleidoscope**. Pattern-based modes color a text mask through the selected palette; Rainbow letters walks the selected palette glyph-by-glyph; Solid uses one selected-palette color. The same treatment/palette combination is used in the configurator previews and in live karaoke over album art.

The startup artwork-karaoke blink is also addressed: over-art coloring is initially rendered as a static frame and does not start its animation loop until the first usable spectrum frame exists. If spectrum analysis is intentionally disabled/not needed, the gate opens immediately. This avoids competing Tk/ImageTk animation during the heaviest analyzer startup interval.

Regression coverage verifies the 15-mode catalog, exactly twelve additions, per-style palette normalization/persistence and dropdown wiring, exclusive configurator pause state across terminal/web/art karaoke/analyzer paths, viewport-only preview animation, and the startup spectrum-ready gate.

## V176 — responsive coloring configurator + large live hero preview

V176 changes the artwork-lyric-coloring configurator so maximizing the window actually uses the available space instead of leaving a large gray dead area. A dedicated **live hero preview** now occupies the top of the configurator. It defaults to the coloring mode currently active in the album-art popup and animates continuously at the configurator refresh cadence. The hero deliberately renders a very large **single-line truncated pangram** rather than shrinking the entire sentence until it becomes tiny, so Plasma and the other coloring modes are easy to see in motion. Plasma rendering crops the alpha mask to the actual text bounds before creating the animated color field, keeping the large preview responsive.

Each style row now has a **📺** button with a `Show` mouseover tooltip. Pressing it changes only the hero preview; it does not change the active artwork coloring mode, Favorite state, or Default selection. The currently shown mode is indicated in the hero heading and by the pressed state of its 📺 button. Opening the configurator initially sets **Shown = the mode currently being used**.

The scrollable style table is now vertically responsive. The embedded table stretches to at least the visible scroll viewport, each style row has vertical weight, and each preview cell expands with its row. The hero takes a guaranteed minimum stage while the style browser receives most additional maximized-window height. Existing row semantics remain: clicking a style name or row preview makes that mode active; Favorite remains multi-select; Default remains exclusive and persisted.

The regular row samples also use more of their available height: Plasma uses roughly 36% of row height for its font target and the Tk text modes roughly 34%, while the hero uses roughly 56%/54% respectively. The V173 incremental scheduler remains: the hero animates every tick and only one row sample advances every other tick, avoiding the old all-previews-at-once Tk starvation.

Regression coverage verifies the hero stage, independent 📺 Show controls and tooltip, maximized-window vertical expansion, huge/truncated hero text, cropped Plasma work, and V176 build identity.

## V175 — hard stop, restored idle-art hotkey, focus-only borders, larger color previews

V175 is a focused control/UI correction on V174. **Ctrl+C and Ctrl+Break now commit to an immediate hard FFplay kill as soon as PAFPlayer receives the stop signal.** Final Stop/Quit actions use the same hard-stop path; seek, pause, and restart operations still use the ordinary graceful terminate/restart path. This removes the one-second graceful wait after PAFPlayer already knows the user is stopping.

The artwork-idle shortcut is restored to **Ctrl+Alt+I**. Manual idle mode ignores system input for the first **3 seconds**, allowing the triggering mouse/keyboard gesture to finish and be put down before activity is allowed to cancel the gallery. The unrequested smart-HUD toggle moves to the temporary **Ctrl+Alt+Numpad1** binding. Shift+Ctrl+Alt+I remains tolerated as a backward-compatible route to the same idle-art action.

Artwork focus chrome is strengthened on Windows 10: the existing monitor-scaled 5px canvas border remains chroma-key transparent while unfocused, and the native-window region suppression is reapplied on focus transitions. The native region clips one physical pixel while focused and **two pixels while unfocused**, removing the inactive one-pixel frame that Windows 10 can redraw just inside the previous clip.

The live lettering samples in the artwork-color configurator are now about **3× larger**. Preview canvases grow from the old 78px height to 216px, and the pangram is rendered as two large centered lines (`Sphinx of black quartz,` / `judge my vow.`), preserving Plasma, Rainbow letters, and Solid white animation while keeping the configurator scrollable.

Regression coverage includes immediate hard-stop behavior, Ctrl+Alt+I + 3-second idle grace, Ctrl+Alt+Numpad1 smart-HUD routing, inactive native/canvas border suppression, and the enlarged two-line coloring preview.

## V174 — nonblocking album-art chrome + persisted play/pause state

V174 fixes the Windows 10 artwork-popup hang shown in the supplied `PAFPlayer — … (Not Responding)` capture. The problem was not the color configurator scheduler itself: the album-art root window was still doing synchronous native-frame clipping from its Tk `<Configure>` callback. V172/V173 could call `SetWindowRgn` more than once for a single configure event, and Windows can answer a region/nonclient change with more configure work. That feedback loop can starve Tk before the client area paints, producing the black unresponsive popup.

Native one-pixel-border suppression is now **coalesced and idempotent**. Static DWM/extended-style cleanup runs once per HWND; the Windows-10 one-pixel region fallback runs only after the window size has settled and only once for each distinct outer size. `<Configure>` merely schedules the work and returns to Tk immediately. The existing focus-only 5px artwork border, transparent aspect gutters, caption/control behavior, resizing, and coloring configurator remain otherwise unchanged.

V174 also persists the actual playback pause state. `PlaybackPaused` defaults to `0`, so existing installations and missing registry values start **playing**, not paused. Entering pause stores paused state; resuming stores playing state; the next PAFPlayer process starts in the state from the previous clean exit. In particular, **if PAFPlayer was playing when you quit, it starts playing next time**. Track handoffs inherit the live state as well.

Regression coverage now specifically asserts that the artwork `<Configure>` path never calls native region clipping synchronously, that native border work is debounced and keyed by HWND/outer-size, and that play/pause persistence defaults to playing and is wired through the session state.

## V173 — responsive coloring configurator, console-focus restore, and safe Q behavior

V173 is a focused reliability patch on V172. The artwork-letter-color configurator no longer tries to repaint every live preview in one Tk callback. It now paints **one preview per event-loop turn** in fair round-robin order, pauses expensive preview work while hidden/minimized, builds the table while withdrawn, shows it only when construction is complete, and cancels its scheduled callback on close. This directly addresses the reported Windows hang while preserving the same scrollable all-style configurator and Favorite/Default settings.

PAFPlayer now captures the foreground terminal HWND **before** the album-art Tk thread is started. Tk root creation and the first artwork show can transiently take Windows focus, so V173 explicitly returns foreground ownership to that captured console after initialization/first-show attention handling. The result is that ordinary console keys such as Space are ready immediately after startup instead of requiring a click back into the terminal. Explicit later artwork-foreground commands are unchanged.

Bare **Q now behaves like INS** and opens the same indexed add/queue-next search. The safety quit gestures are **Q Q Q**, **Ctrl+Q**, **Alt+Q**, or **Ctrl+Alt+Q**. The triple-Q path is integrated with the Q-opened picker: the second Q is still valid query text unless a third consecutive Q follows it, so normal searches beginning with `q` remain possible. Modified-Q also quits from inside the picker. Bare Q no longer turns the DEL confirmation into an application quit.

V173 otherwise preserves V172 web transport, 20 Hz spectrum endpoint, artwork rendering/chrome, lyric-color modes, HUD packing, playback, history, and visualizer behavior.

## V172 — 20 Hz web spectrum, artwork-color configurator, and cleaner popup chrome

V172 concentrates on the web controller and the external album-art/lyrics window.

### Web controller

- The startup/transient server announcement includes the running build, for example `PAFPlayer v172 webserver`, so the active version is visible without opening Help or `--version`.
- The classic transport's middle button is now a true pause/resume toggle. Its glyph follows state (`⏸︎` while playing, `▶` while paused), and clicking it uses the same `pause-toggle` action as the keyboard instead of a pause-only web action.
- Browser spectrum transport is split away from the larger `/api/status` JSON. A compact `/api/spectrum` endpoint is published and polled every 50 ms (20 fps), while ordinary metadata/control status keeps its lower-rate poll. The web spectrum is still derived from PAFPlayer's real FFmpeg analyzer/visualizer-mode pipeline; only the browser transport cadence/payload changed.

### Album-art popup chrome and aspect fit

- The focus-only 5-pixel artwork border remains. V172 also suppresses the thin native outer-edge border as far as the active Windows composition path permits, with a clipped one-pixel fallback for older Windows chrome while retaining normal resize behavior.
- When `object-fit: contain`-style artwork would otherwise leave transparent side/top/bottom gutters, PAFPlayer may transiently shrink the popup to the fitted image rectangle. The width will not shrink far enough to hide the control strip. The user's saved/manual geometry remains authoritative and is restored/reconsidered for later artwork rather than replacing the saved size with the temporary compact size.
- Both visible song/title fields in the popup chrome are centered within the space assigned to them. The client title label uses true centered layout; the native caption uses measured padding because the Windows-owned caption text itself does not expose a normal Tk alignment control.

### Artwork lyric-color configurator

The focused title strip now shows the current coloring mode as a clickable name rather than a dropdown with two adjacent checkboxes. Clicking the mode opens one scrollable configurator containing every artwork-karaoke letter-coloring type.

Each coloring type gets a two-row, two-column card:

- top left: the coloring-mode title, right-justified in the left half;
- top right: a live animated preview of `Sphinx of black quartz, judge my vow.` using that mode's actual coloring behavior;
- bottom left: global options — `Favorite` is a checkbox and `Default` is an exclusive radio choice;
- bottom right: the per-style-options area, currently intentionally empty/placeholder-ready for future style-specific controls.

Clicking a mode title or its preview makes that mode active immediately. Multiple modes may remain Favorite; exactly one is Default. Existing `ExternalAlbumArtKaraokeColorFavorites` and `ExternalAlbumArtKaraokeColorDefaultMode` persistence is retained.

V172 does not intentionally change terminal HUD packing, audio processing, Last.fm/history semantics, the terminal visualizer, playlist behavior, or unrelated hotkeys.

## V171 — karaoke coloring Favorites + Default

V171 changes only the focused external-art karaoke coloring selector. Beside the existing `Color:` dropdown, the control strip now shows `Favorite` and `Default` checkboxes. `Favorite` is independent for each coloring mode, so multiple modes can be marked at once. `Default` is exclusive: exactly one coloring mode is the startup default; checking it on another selected mode moves the default designation there. Selecting a dropdown entry refreshes both checkboxes to show that mode's saved state.

Favorites are stored in `ExternalAlbumArtKaraokeColorFavorites`; the default is stored in `ExternalAlbumArtKaraokeColorDefaultMode`. Until a user explicitly chooses a default, startup preserves V170's last-used coloring-mode behavior. No rendering, lyric layout, zoom, transparency, HUD, playback, visualizer, hotkey, or unrelated UI behavior is changed.


## V170 — focused transparent artwork + plasma karaoke

V170 refines the persistent external album-art window around the supplied NOFX capture. The image rectangle remains user-owned and never crops the source, but **unused aspect-ratio area is now transparent instead of black**. The main art canvas and idle related-art windows use a Windows chroma key; Pillow-backed crossfades are composited into transparent RGBA frames, so a portrait/square image inside a wider popup exposes the desktop in the unused gutters rather than manufacturing letterbox bars.

The monitor-scaled artwork border still reserves the same pixels, so focusing/unfocusing cannot move or resize the image. Its color is now a focus cue: the border is visible only while the external art top-level owns foreground focus and is chroma-key transparent otherwise. The native Windows caption/control strip remains conventional.

Over-art karaoke now has a persistent font zoom. While the artwork window is focused, `Ctrl+MouseWheel`, `Ctrl+-`/`Ctrl+_`, and `Ctrl+=`/`Ctrl++` change the lyric scale; small `−` and `+` buttons appear in the art control strip **only while focused**. Zoom is clamped to 50–250% and stored in the existing PAFPlayer registry key. Lyric layout now fits and clamps the complete text block inside safe canvas margins, shrinking only when required to keep every line—including descenders and the final line—from being cut off.

A new coloring dropdown offers **Plasma** (default), **Rainbow letters** (the V169 per-glyph behavior), and **Solid white**. Plasma is not a one-color-per-letter cycle: PAFPlayer renders a real text mask and fills its pixels from an independently animated two-dimensional sine-wave plasma field, so color varies *within* each glyph and flows through the words. Its timer replaces only the lyric image item and never decodes or repaints the cover image or writes to the terminal.

The V169 information-first HUD optimizer (currently toggled with Ctrl+Alt+Numpad1), V167 Unicode recovery, progress-glyph protection, playback, visualizer, Last.fm, history, and artwork geometry behavior are otherwise unchanged.

## V169 — information-first smart HUD layout optimizer

V169 replaces the growing collection of rigid HUD-column special cases with a cached two-row layout optimizer. The rule is deliberately hierarchical: **show all metadata at full value width first; beautify the result only with space that is genuinely spare.** The optimizer searches row assignments and semantic colon-pair alignments for the metadata actually present on the current track. `Act/Year`, `Song/Genre`, `Album/Original artist` (or `Album/Last play` when appropriate), and `Comment/Composer` are rewarded for sharing colon columns, but those alignments are soft. If an alignment would make a row overflow, the candidate loses and PAFPlayer is explicitly allowed to break the grid rather than lose information or manufacture a third row. Narrow/complex cases that cannot preserve every field in two full-width rows fall back to the established wrapping/dense renderer.

The optimizer is geometry-cached by terminal width and rendered field widths, so animated Artist/Song recoloring does not rerun the search every frame. Inline `Last play:` remains a second pass over the resulting real metadata colons; its preferred right-side anchors therefore benefit from the optimized grid. The supplied Dead Kennedys, Dethklok, Uncle Outrage, Dreadnoughts, and Bride Riot captures are executable regression cases. Bride Riot specifically asserts four free colon pairs (`Act/Year`, `Song/Genre`, `Album/Original artist`, `Comment/Composer`), while a 104-cell version of the same data asserts the opposite rule: every field stays visible even though several colon pairs must become deliberately ugly.

The source-level switch is `HUD_SMART_ALIGNMENT_ENABLED = True` beside the other display/program flags. `ALIGN_INLINE_LAST_PLAY_TO_HUD_COLONS` remains as a source-compatibility alias. `Ctrl+Alt+I` toggles the whole smart HUD optimizer plus inline Last-play alignment for the current process; `Ctrl+Alt+Shift+I` keeps the older immediate idle-art routine.

## V168 — smart inline `Last play` colon alignment

V168 keeps the existing width-aware HUD packing, then performs a second alignment pass only after the rest of the metadata HUD has been constructed. When `Last play` is inline on the `Play:` row and spare width exists, PAFPlayer moves `Last play:` rightward so its colon exactly reuses a real metadata colon from the rows below. Right-side tail fields (`Composer`, `Comment`, `URL`, and `Original artist`) are preferred; if none can be reached without overflowing the terminal, the nearest usable semantic colon such as `Year`, `Genre`, `Album`, `Song`, or `Act` is used. If no alignment fits, the historical three-space gap is retained. Value punctuation such as URL/title colons is never treated as an alignment stop.

The source-level default is `ALIGN_INLINE_LAST_PLAY_TO_HUD_COLONS = True`, placed with the other top-level display flags. `Ctrl+Alt+I` toggles the behavior for the current PAFPlayer session and the state follows track handoffs. The old focus-only immediate idle-art command moves to `Ctrl+Alt+Shift+I`. Four real-session HUD captures supplied for V168 are encoded as unit-test fixtures, including the Dead Kennedys and Dethklok Composer alignment cases, the Uncle Outrage Composer/Comment-tail case, and the Dreadnoughts fallback to an available semantic colon.

## V120 preservation release

V120 is rebuilt from the verified V112 app-and-docs archive, not from V113 or the failed V114–V119 terminal branch. V112's terminal renderer, visualizer timing/output, global physical-key polling, Pause behavior, and mouse/wheel handling remain the atomic baseline. V120 adds only isolated ledger work: one shared verified ReplayGain baker used by PAFPlayer and `audit_music_batch.py`; atomic helper recovery; focused `Ctrl+Alt+B` bake/resume; exact-row SQLite history verification and visible failure state; default-on Frequency Warp semantics; `✅Learned`; `SigAur`; adaptive sectioned controls; J/Q playlist queue selection; `--catalog-file`; and corrected Help diagnostics/directory behavior.

The ledger's Windows-live-only artwork/floating-lyrics changes, extra-row ownership changes, and web visualizer refinements are intentionally not claimed as proven in this build. They remain gated on the two-minute Windows Terminal/MSYS checklist in the release-specific documentation.

## Quick start

```bat
play_audio_file.py C:\mp3\song.flac
play_audio_file.py C:\mp3\lists\favorites.m3u
play_audio_file.py --help
```

During playback, `?` or F1 opens the compact live key map. `--help` is the definitive command-line spelling reference; `--version` and `--which-script` identify the exact executable on `PATH`.

## Runtime and platform

Normal operation is Windows-oriented: registry persistence, `msvcrt` key reads, Windows Terminal features, `os.startfile`, optional Winamp control and the Tk art window are deliberate. FFplay is the audio process; FFmpeg performs analysis, resampling and selected extraction; FFprobe supplies one cached metadata/duration result per file. `wcwidth` is optional, with an internal width fallback. Claire helper modules are loaded locally/importably and, on Windows normal playback, may be downloaded beside the script when missing; unit tests suppress network bootstrap. Mutagen is optional but expands raw tags, embedded art, ReplayGain formats and lyric-tag round-trip support.

On first Windows use, if `C:\mp3` is absent, PAFPlayer asks for the actual music collection and can create `C:\mp3` and `C:\music` junction aliases plus `C:\mp3\lists`. Existing paths are not silently replaced.

## Session architecture

`main()` handles special utilities first, establishes collection aliases and global attribute rules, loads registry settings, parses options, starts the loopback web server and external artwork owner, then enters direct-file, random, autoplay or playlist navigation. Playback is owned by one state machine. Keyboard input and HTTP requests produce the same semantic action strings; web request threads never mutate the playback state directly. Track transitions persist settings and resume state, rotate queue history, and cleanly close the catalog index, web server, art window and Winamp guard in `finally`.

Long-latency work is deliberately off the playback path: catalog indexing/reconciliation, history prefetch, shuffle-cache serialization, Last.fm calls, artwork downloads, spectrum analysis, large-playlist loading/rebuilds and artwork GUI work use threads or subprocesses. Generation tokens, locks and a bounded action queue prevent stale async art or web actions from taking ownership of the session.

PAFPlayer adds structured, thread-safe diagnostic observability without turning the terminal into a log sink. `C:\logs\PAFPlayer\errors.log` stores contextual failures and complete tracebacks; `C:\logs\PAFPlayer\trace.log` stores verbose session, track, FFplay, input, history, shuffle, artwork, lyrics, web and shutdown events. Every record includes a timezone-aware millisecond timestamp, session ID, PID and thread identity. Error summaries are mirrored into the trace timeline. Each active log rotates independently to one adjacent `.bak` before a write would exceed 100 MiB. Uncaught background-thread exceptions are captured without printing over the HUD.

PAFPlayer gives modal console prompts a renderer pump. A prompt that temporarily owns keyboard input polls rather than blocking in `getwch()`, checks Ctrl+Break, and services the visualizer between keypresses. Prompts drawn over the HUD use ANSI blink so they cannot be mistaken for ordinary status text. The external Tk artwork interpreter is still destroyed on its owner thread; PAFPlayer additionally cancels all stored lyric/mouse timers, collects Tk cycles on that same thread, waits for shutdown acknowledgement, and suppresses the known late Windows Tcl `Tcl_AsyncDelete` finalizer diagnostic only after normal process cleanup has finished.

## Audio pipeline

Every FFplay launch receives a start offset, optional duration cap and user volume up to 100%. All signal processing is expressed as one `-af` chain. PAFPlayer orders that chain as: ReplayGain `volume=` first; speed `atempo` factors; a separate boost filter only when user volume exceeds 100%; balance `pan`; optional 5.1/7.1 expansion; then `aresample=192000` (with a 96 kHz fallback) last. The source no longer places a standalone decoder-side `-ar 192000` before input. Source sample-rate interpretation remains intact while only filtered output is resampled.

ReplayGain is enabled by default in track-preference mode. A track visit resolves an immutable `ReplayGainInfo` once and reuses it through seek, pause/resume, output, balance, volume and speed restarts. Track preference falls back to album gain; album preference reverses this. Only standard track/album gain and peak fields count. Malformed, non-finite or prose values are rejected. Clipping prevention is exact: `ceiling_db = -20*log10(peak)` and `applied_db = min(requested_db, ceiling_db)`. Ordinary playback never rewrites the file. `Ctrl+Alt+B` is the explicit exception: after Y confirmation on FLAC/MP3 it stops audio, bakes through `ClaireAudioProcessing.py`, validates and verifies a timestamped backup/replacement, rolls back on failure, and resumes at the same position.

Non-destructive edge trimming scans at most 60 seconds at each edge, defaults to -43 dBFS, requires 0.35 seconds of continuous quiet and retains 0.08 seconds as a safety pad. Mid-track silence is untouched.

## Metadata, HUD and title

One cached FFprobe pass obtains duration plus format/stream tags. Normal metadata uses Artist (with album-artist fallback), Song, Album, Year, Genre, Original artist, Composer, URL and Comment. Missing Song falls back to a cleaned filename; selected malformed ID3 fields are repaired only when their normal value is absent. `Alt+3` is a human-oriented view of the broader cached ffprobe map and, for MP3 with Mutagen, raw frames: HUD-equivalent fields come first, common container keys and ID3 codes receive English meanings while retaining raw identity, and fingerprints/lyrics/binary diagnostics are pushed later. Every field occupies one terminal row; multiline or over-width values end in `...` instead of wrapping through the page. This is a nonblocking persistent player view: playback and navigation remain live, automatic completion advances normally, and each new track replaces the visible page with its own tags. PgUp/PgDn changes tag pages; Alt+3, Esc or Q closes the view.

The HUD is an information-packing problem, not a rigid table. PAFPlayer first tries to append `Last play` to the Play row, using the full path when it fits and the filename form when only that fits. For the metadata rows, V169 searches complete two-row candidates using the fields actually present on the track. Candidates that drop, truncate, or overflow a field are rejected before aesthetics are considered. Among the full-information candidates, the normal semantic row (`Act/Song/Album/Comment` above `Year/Genre/Original artist/Composer`) is preferred, and matching semantic colon pairs are aligned whenever the extra padding still fits. If the terminal is tight, the optimizer is intentionally willing to move a field or break colon alignment to keep more information visible; if no complete two-row candidate exists, the established dense/wrapping fallback takes over. Inline `Last play:` is then aligned against the real surviving metadata colons when that can be done without overflowing the Play row. PAFPlayer leaves the Last play value blank only while its cold SQLite lookup is pending, then resolves it to the stored compact date/age or the definitive `Never` result. That resolved value is a snapshot of history at track start: earning the current visit at 33% updates SQLite for the next visit but never changes or reflows the current HUD. `Never` is faint, warm and italic. The display-width engine accounts for emoji, combining marks and ANSI/OSC sequences.

The compact `?`/F1 Help masthead places the effective `Tags:` line immediately below `Last play:`, then ReplayGain/playlist diagnostics and their divider before the key map. Pressing D while Help is open toggles a current-directory line. When both exact tags `instrumental` and `instrumentals` are effective, display renderers merge them into one `instrumental(s)` entry without changing either source rule; the synthesized entry is rendered 25% brighter than its ordinary color. Effective `learned` additionally produces `✅Learned`. `Ctrl+Alt+/` persistently toggles three live HUD rows for ReplayGain, playlist, and the same effective tags. Those rows borrow their space from the visualizer and return it when hidden.

The Windows Terminal title is exact shared state: it contains the playback state plus the song or active lyric marquee, without the old trailing “play_audio_file” suffix, and is mirrored by the external art window and web UI. Speed is omitted at untouched 1×, appears when non-default, and remains visible for the process after any speed control has been used.

## Karaoke, progress and visualizer

Lyrics are discovered from exact-stem sidecars and embedded tags, with timed formats preferred when usable. Karaoke rendering combines 21 typography styles, 7 color treatments, EmojiMaxx substitutions, width-aware wrapping and configurable visualizer compositing. `Ctrl+E` opens sidecars in the configured text handler; `D` reloads them and, with Mutagen, writes/reads embedded lyric fields to verify the round trip.

The console spectrum combines 30-Hz analysis with a target repaint rate of 120 Hz through interpolation, duplicate suppression and throughput adaptation. DRCS is enabled by default; SIXEL is disabled by default. The source defines 25 glyph families, 15 spectrum treatments, 65 processing styles, 32 palettes, 4 fade/color-aging styles, 12 persistence styles and 3 horizontal granularities. The default hides only the highest one visualizer row while still analyzing it. Rendering anchors at terminal column one and temporarily suppresses autowrap to prevent right-edge drift. PAFPlayer anchors every PAFPlayer HUD row with an absolute viewport-relative `CUP` sequence on Windows instead of the terminal-global `CSI s/u` saved-cursor slot. This prevents Chafa/DRCS/terminal activity from redirecting later metadata, progress and karaoke repaints to the visualizer's last cursor position. Console text and byte transports also share one reentrant write lock, so a worker callback cannot split a VT control payload.

## Artwork

Artwork priority is cover, back, disc/CD, inlay, then other/matrix. Exact-stem and folder-gallery behavior is protected by duplicate hashing and loose-folder heuristics. PAFPlayer adds a strict rule: if any path component is named MISC, only embedded art from the current audio file and its exact-stem sidecars are eligible. Generic cover/back files, unrelated track art and VLC cache art are excluded, and extracted embedded art materializes under the exact track stem. This rule is shared by console/web art, the popup and idle gallery.

The persistent Tk popup is withdrawn when no art exists and shown again when a later track has art. Turning external artwork on also deiconifies and raises it immediately; it does not wait for a separate foreground command. Its title mirrors the exact live player title. A manual mouse move becomes authoritative immediately and remains the saved position across art changes, idle initialization, hide/show cycles, tracks, sessions, and restarts. Idle drift uses separate transient geometry; the live user geometry is captured before drift and restored afterward instead of falling back to an older startup or registry position.

The popup rectangle belongs to the user. Ordinary resizing is free-form and the chosen width, height, and position persist. Holding Ctrl during a resize forces a 1:1 square; releasing Ctrl restores free-form resizing without undoing the square. Loading or rotating artwork never changes the popup dimensions. Every image is contained inside the existing drawable rectangle without cropping; unused space is black, producing top/bottom or side bars when image and window ratios differ. The border is five pixels at 96 DPI and scales per monitor (for example, eight pixels at 144 DPI and ten at 192 DPI). Triple-left-click opens a content-hashed temporary copy under `%TEMP%\PAFPlayer\album-art-view` with the OS default viewer, leaving the music folder untouched. Active playback may crossfade weighted related images; an idle foreground/dance gallery can be triggered explicitly or after the configured idle interval.

The artwork client area has a conventional header directly below the untouched native Windows caption. It displays centered track text plus a raised three-way Lyrics control—`Lyrics: Over Artwork`, `Lyrics: Floating`, `Lyrics: Both`. Both can render the same cue simultaneously. A conditional `🔡` button opens the over-art lettering profile and a conditional `🔠` button opens the independently persisted floating-lettering profile; both buttons appear in Both mode. Each profile uses the full 15-style configurator with Enabled/Default/Favorite, per-style palette, per-style speed, and optional MiniLyrics-like timed emphasis. Focus-only lyric zoom controls continue to affect over-art text size. Plasma is a per-pixel animated 2-D field inside a fitted text mask rather than one flat color per character. The artwork window avoids full-cover animation; cue/zoom/color changes replace only lyric items, and the plasma timer updates only its lyric image. PAFPlayer gives image decode and lyric drawing independent exception boundaries: a Tk/font/Unicode lyric error cannot discard a valid cover or falsely display `Album art could not be decoded`. Over-art lyrics are fitted and vertically clamped so the final line and descenders stay inside the canvas. Floating lyrics display `Waiting for lyrics…` until the first cue. The floating window is transparent, independently sized/positioned and saved separately. Right-clicking visible lyric text exposes a persistent Always on top toggle. Visible glyphs are interactive while transparent space passes clicks to the application below; holding Ctrl makes the whole surface interactive, allowing movement from empty space and edge/corner resizing. Its native `WM_NCHITTEST` forwarding uses pointer-width-safe `ctypes` signatures. PAFPlayer also catches errors inside that ctypes callback, safely forwards the window message and logs the complete traceback without writing over the terminal. Current lyrics are published during active and paused playback even when the web server is disabled.

PAFPlayer repairs the constructor error that blocked both GUI lyric modes on the reported Windows Tk build. `tkinter.font.Font` receives its interpreter owner through the supported `root=` parameter for the waiting, floating and over-artwork fonts. The former `master=` keyword was being forwarded to Tcl as an invalid `-master` font property, producing the recorded callback warning before any glyph could be drawn.

Missing-art download is explicit only: `Ctrl+Alt+D` starts a daemon lookup against MusicBrainz and the Cover Art Archive, rate-limited at roughly one request per second. It validates image signatures, caps payload size, writes atomically and saves exact-stem art in MISC or `cover` art elsewhere. The attempt database supports an eight-second second-press retry confirmation. No cover is downloaded automatically.

## Web controller

`PAFWebServer` is a dependency-free `ThreadingHTTPServer` with a self-contained HTML/CSS/JavaScript client. It is enabled by default at `127.0.0.1:666`; bind failure is nonfatal. The page exposes exact title/tags, seekable progress, live lyrics and spectrum, transport, speed/volume/balance/output, modes, toggles and related art. POST actions are allow-listed or parsed as bounded setters and enter a 64-item semantic action queue consumed by the playback owner.

PAFPlayer places karaoke immediately above a dedicated independently scrollable Choices region containing Choices, toggles, other actions and metadata. Wrapped lyrics grow their reserved area immediately and push that region downward. Extra lyric height contracts only after it has been unused for 30 seconds and the mouse has also been idle for 30 seconds; later wrapping cancels the pending contraction.

Loopback is the safety boundary. There is no authentication or TLS. Explicitly binding `0.0.0.0` makes metadata and playback control reachable to other clients permitted by the host firewall/network and should be a deliberate trusted-LAN choice.

## Playlists, local history and Last.fm

Playlist formats are M3U/M3U8, PLS and XSPF. A single positional playlist is promoted to playlist mode; mixing it with other positional files is rejected. Lists over 5,000 entries defer filesystem existence checks. The queue is persistent and history-biased: departed tracks rotate to the tail, the original queue-build timestamp controls the five-hour cache lifetime, and writes coalesce asynchronously. PAFPlayer distinguishes an earned play from a shuffle visit. A launch/visit is recorded immediately in a separate recent-visit ledger and makes even a sampled/skipped track ineligible for shuffle for three hours whenever another candidate exists. The queue JSON no longer stores or restores stale `last_played` snapshots; current history comes from SQLite/prefetch. PAFPlayer earns local Last play at one-third of the merged unique timeline while Last.fm remains strictly above 50%. A one-track or alias-heavy list replays safely rather than terminating. Resume near the final five seconds restarts at zero.

INS **or bare Q** searches a background catalog with word-any-order matching. PAFPlayer physically validates and deduplicates the catalog only when it is loaded or reconciled, then publishes immutable pre-casefolded search records. Each typed query is purely in-memory and cached; a one-character query no longer repeats tens of thousands of `stat()`/`samefile()` calls. Optional stale-list filesystem reconciliation waits until at least three query characters exist and never holds the search lock during disk I/O. The INS/Q chooser is confined to rows above the visualizer and pumps it while waiting. Three consecutive Q presses quit; Ctrl+Q, Alt+Q, and Ctrl+Alt+Q quit immediately. Shift+INS uses a multi-select Windows file picker. Every successfully added selection enters a separate play-next queue; one item is next, and several are randomized among themselves when shuffle is active before ordinary history-biased playback resumes. Successful insertion resets playback speed to 1×. DEL shows a blinking Y/N prompt, polls Ctrl+Break, keeps the visualizer active, rewrites playlist membership only after confirmation, and never deletes the audio. Runtime tombstones/addition overlays prevent older background rebuild snapshots from resurrecting a removed track or losing a new one. PgUp/PgDn opens the playlist browser; Enter jumps to the selected file. Ctrl+O loads a new playlist through a clean relaunch.

Local play history is written immediately at one-third of unique source duration heard; normal Last.fm scrobbling still requires more than 50%. Merged listened ranges prevent seek inflation for both. Marking a track learned force-writes local Last play without submitting a scrobble. Last.fm Now Playing is separate and sent once when each logical visit begins. `Ctrl+Alt+S` can force both local history and a scrobble, with a second-press confirmation if the visit has already been scrobbled. On Windows the single default database is `C:\bat\play_audio_file-play-history.sqlite3`, even before it exists, so versioned script locations cannot fork history. Log import can generate CSV and a grouped terminal report.

## Attribute workflows

Claire attribute rules are evaluated from root to local `attrib.lst` files, then the cached global `C:\mp3\mp3-base-attributes.lst`. Selectors match normalized relative path, filename or full path; an empty selector is global. Plain/`+`/`++` assignments add or whitelist, while `-`/`--` remove or permanently blacklist according to existing permanence rules.

`Ctrl+Alt+L` creates a collision-conscious selector for the current file and prompts for optional safe extra tags. An untouched prompt expires after ten seconds; once typing begins, the idle limit becomes thirty seconds. Only Enter commits extras. Esc, timeout or a second hotkey discards them. The visualizer remains active during the prompt. The append payload intentionally contains a blank line, timestamp comment, rule and trailing blank line. `Ctrl+A` opens the applicable attribute file, including the nearest inherited parent after an Already learned result.

## Current controls

| Area | Current contract |
| --- | --- |
| Transport | Space/Pause/media play-pause; X, Ctrl+W, Alt+F4, Ctrl+C or Ctrl+Break stop; Left/Right seek 5 s, Shift 15 s, Ctrl 60 s. Bare media Previous/Next seeks 10 s; Shift seeks 80 s; Alt, Ctrl or Ctrl+Alt changes track. |
| Track navigation | < and > previous/next track; { and } previous/next audio directory; PgUp/PgDn visit/future browser; A autoplay; R shuffle. |
| Playlist editing | INS or bare Q cached/preindexed search/add/queue-next; QQQ quits; Ctrl+Q, Alt+Q, or Ctrl+Alt+Q quits immediately; Shift+INS multi-select Windows picker/add/queue-next; DEL removes playlist membership only; PgUp/PgDn browse and Enter jumps; Ctrl+O loads a new playlist; Ctrl+R reloads/rebuilds. |
| Audio | +/− speed; `=` resets volume to 100% and speed to 1×; every startup/new-playlist relaunch and successful INS addition starts/resets at 1×; Up/Down volume ±5%, Shift ±20%; global Ctrl+Alt+Up/Down volume ±5% even when another application has focus; NumPad 4/6 balance and 5 center; 2/5/7 output channels; L loop. |
| Lyrics and metadata | Ctrl+E edit sidecars; D reload/write embedded lyric tags and verify; Alt+3 persistent live one-row tag view with common ID3 meanings; PgUp/PgDn pages; Alt+3/Esc closes; Ctrl+U/Ctrl+B URL chooser. |
| Attributes/history | Ctrl+A attrib.lst editor; Ctrl+Alt+L learned prompt plus local Last play update; local history earns at 33% only after commit plus exact-row readback; a failed verification is logged and shown; Last.fm remains >50%; Ctrl+Alt+S force local history + Last.fm scrobble. |
| ReplayGain bake | Ctrl+Alt+B prompts before using the shared verified baker on FLAC/MP3; peak protection, backup, validation, replacement and rollback are owned by `ClaireAudioProcessing.py`. |
| Art | Alt+A or Ctrl+Alt+NumPad8 popup; Ctrl+Alt+A raise; Ctrl+Alt+I idle gallery (3s input grace); Ctrl+Alt+D explicit missing-art download / historical DRCS fallback. The artwork-header Lyrics button cycles Over Artwork / Floating / Both; Both renders both destinations simultaneously. `🔡` appears when over-art lyrics are enabled and `🔠` when floating lyrics are enabled. Each opens an independent 15-style lettering profile with Enabled/Default/Favorite, keyboard-cycleable palette, per-style speed and timed emphasis. Ctrl+Alt+F toggles inclusion of floating lyrics. Ordinary resize is free-form and holding Ctrl forces 1:1. Images are contained without cropping, unused aspect-ratio gutters are transparent, and the art border is visible only while focused. Focused Ctrl+wheel, Ctrl+-/_, Ctrl+=/+ and focus-only −/+ buttons change the persisted over-art font scale. |
| Visualizer | V, F6/F7, Shift+F6/F7, Alt+F6/F7, Shift+F4, C/Shift+C, Alt+Shift+C, Ctrl+G, P and favorite controls traverse independent rendering axes. |
| HUD/help/defaults | Ctrl+Alt+Numpad1 toggles information-first smart HUD packing/colon alignment; ? or F1 help; Help shows Last play, Tags, ReplayGain/playlist, then the divider; D toggles its directory line; Ctrl+Alt+/ toggles ReplayGain/playlist/tags HUD rows; first F5 redraw preserves Chafa, a second within 3 seconds clears it, and Ctrl+Alt+F5 always clears it; * defaults manager; Ctrl+Alt+F1 restore all; Alt+F1 undo. |

## Command-line surface

The built-in usage remains the definitive option spelling. Principal modes are direct file, `--playlist/-p`, `--random-file/-r`, `--random-file-recursive/-R`, `--unit-tests/-t`, `--emoji-display-test/-e`, lyric-corpus processing, playlist-history analysis, and Last.fm history generation/display. `--catalog-file PATH` selects the INS catalog; if an explicitly selected catalog is missing it is built atomically in a background thread from the configured music root. Runtime switches cover loop, karaoke, ReplayGain, edge trim and thresholds, shuffle lifetime, throb periods, genre emoji, initial blank line, DRCS/SIXEL/all visualizers, fade, top-row truncation, target FPS, album art, external art/idle interval, web enable/host/port, attribute management and now-playing outputs. Invalid playlist/file combinations and malformed values fail with exit code 2 rather than entering FFplay ambiguously.

## Files and persistence

| Purpose | Current location/rule | Notes |
| --- | --- | --- |
| Settings | HKCU\Software\ClaireCJS\play_audio_file | Player state, favorites, defaults, resume data, preferred art-window geometry, V180 Artwork/Floating/Both lyric mode, over-art lyric font scale, independent artwork and floating lettering modes/favorites/defaults/palettes/speeds/timed-emphasis masks, and floating-lyrics geometry. |
| Play/visit history | C:\bat\play_audio_file-play-history.sqlite3 | Canonical Windows local-history database; 33%-earned/learned Last play is separate from >50% Last.fm and immediate shuffle visits. |
| Shuffle cache | %TEMP%\play_audio_file\shuffle_cache\<hash>.json | Five-hour original-build lifetime and persistent queue order; writes coalesce asynchronously; no history timestamp authority. |
| Spectrum cache | %TEMP%\play_audio_file\spectrum_cache | Reuses analyzer results. |
| Art attempts | %TEMP%\PAFPlayer\album-art-attempts.sqlite3 | Records explicit cover-download attempts and outcome. |
| External art viewer copies | %TEMP%\PAFPlayer\album-art-view | Content-hashed temporary files for the OS image viewer. |
| Now playing | C:\mp3\lists\winamp_now_playing.txt/.jpg or play_audio_file-now_playing.dat/.jpg | Winamp-compatible status/art sidecars. |
| Global attributes | C:\mp3\mp3-base-attributes.lst | Cached final rule layer after root-to-local attrib.lst rules. |
| Catalog | C:\mp3\lists\everything.m3u, then C:\mp3\filelist.txt | Indexed source for INS playlist additions. |
| Diagnostics | C:\logs\PAFPlayer\errors.log and C:\logs\PAFPlayer\trace.log | Errors contains contextual failures/full tracebacks; trace contains verbose lifecycle/action state. Both rotate independently to one `.bak` at 100 MiB. A new runtime error shows a blinking `⚠️` beside `?`; Help displays recent warning summaries, both log paths and acknowledges the badge. |

# Display invariants

- `Last play` is resolved once at the beginning of a logical track visit. It is blank only during the cold lookup, then remains the resolved age/date or `Never` for that visit. When inline, V169 may move it rightward after optimized metadata construction to share a real HUD-label colon, but never beyond the terminal width.
- The 33% local-history write and learned action update persistent history without repainting `Last play`; the next visit observes the new record.
- `Dir:` has one renderer and one reserved row only when the full Play line does not fit. Mid-track history writes cannot change that geometry.
- Cell-aware truncation never leaves an opening parenthesis, bracket, brace, angle bracket, or paired quote dangling at the edge. If clipping occurs inside a pair, the matching closer becomes the last visible character.
- Explicitly INS-added tracks outrank resume/history/shuffle successors until the manual queue is empty.
- Playback speed begins at 1× on every process start, clean playlist relaunch, and successful manual playlist insertion.

# Current source-derived catalogs

## Visualizer glyph families (25)

1. Classic, 2. Legacy Classic, 3. Eighth Blocks, 4. Soft Blocks, 5. Dense Blocks, 6. Half Blocks, 7. Thin Blocks, 8. Wide Blocks, 9. Shaded Columns, 10. Stepped Columns, 11. Braille, 12. Dots, 13. Circles, 14. Diamonds, 15. Runes, 16. Stars, 17. Math Symbols, 18. Gothic Marks, 19. Sparkles, 20. ASCII Fine, 21. ASCII Heavy, 22. Digital, 23. Needles, 24. Rounded, 25. Minimal

## Visualizer treatments (15)

1. Punch, 2. Balanced, 3. Soft, 4. Tight, 5. Smooth, 6. Pulse, 7. Skyline, 8. Peaks, 9. Compressed, 10. Expanded, 11. Transient, 12. Valleys, 13. Wide, 14. Hot, 15. Quiet

## Processing styles (65)

1. Vertical Flow, 2. Candy Stripe, 3. Three Bands, 4. Frequency Zones, 5. Checker Spectrum, 6. Plaid, 7. Nine-Patch Quilt, 8. Radial Sweep, 9. Diagonal Sweep, 10. Radial Spectrum, 11. Argyle, 12. Tartan, 13. Log Cabin Quilt, 14. Pinwheel Quilt, 15. Diamond Quilt, 16. Basket Weave, 17. Houndstooth, 18. Chevron Quilt, 19. Mosaic Quilt, 20. Star Quilt, 21. Brickwork, 22. Hex Weave, 23. Confetti, 24. Circuit Board, 25. Zebra Neon, 26. Polka Dots, 27. Stained Glass, 28. Crosshatch, 29. Spiral Quilt, 30. Wave Interference, 31. Flying Geese Quilt, 32. Ohio Star Quilt, 33. Bear Paw Quilt, 34. Tumbling Blocks Quilt, 35. Rail Fence Quilt, 36. Irish Chain Quilt, 37. Drunkard Path Quilt, 38. Kaleidoscope Quilt, 39. Lone Star Quilt, 40. Courthouse Steps Quilt, 41. Storm At Sea Quilt, 42. Snail Trail Quilt, 43. Card Trick Quilt, 44. Prairie Points Quilt, 45. Cathedral Window Quilt, 46. Trip Around World Quilt, 47. Amplitude, 48. Impact, 49. Energy Heat, 50. Transient Flash, 51. Bass Pulse, 52. Midrange Pulse, 53. Treble Spark, 54. Persistence Age, 55. Crest Factor, 56. Spectral Density, 57. Local Contrast, 58. Peak Proximity, 59. Energy Plaid, 60. Dynamic Checker, 61. Loudness Zones, 62. Signal Aurora, 63. Signal Aurora Full Spectrum, 64. Signal Aurora Prism, 65. Signal Aurora Storm

## Palettes (32)

1. Full Rainbow, 2. Pastel Rainbow, 3. Fire, 4. Ocean, 5. Forest, 6. Toxic, 7. Sunset, 8. Magenta-Cyan, 9. Purple-Gold, 10. Red-White-Blue, 11. Cyan-Yellow, 12. Monochrome Green, 13. Monochrome Amber, 14. Monochrome Cyan, 15. Monochrome Violet, 16. Neon Pastel, 17. Heatmap, 18. Plasma, 19. Aurora, 20. Ice, 21. Candy, 22. RGB, 23. CMY, 24. Jewel, 25. Halloween, 26. Vaporwave, 27. Synthwave, 28. Earth, 29. Rose Gold, 30. Electric Blue, 31. Lime-Magenta, 32. White Hot

## Fade/color-aging styles (4)

1. Energy dim, 2. ROYGBIV decay, 3. Hard cutoff, 4. Pulse decay

## Persistence styles (12)

1. Peak Hold + Fall, 2. Ghost Frames, 3. Comet Trails, 4. Heat Memory, 5. Spring / Bounce, 6. Beat Flash, 7. Echo Ladder, 8. Phosphor Glow, 9. Shadow Peaks, 10. Gravity Trails, 11. Freeze + Melt, 12. Waterfall Smear

## Horizontal granularity modes (3)

1. 1× Cells, 2. 2× Half Cells, 3. 2× Twin DRCS

## Karaoke typography styles (21)

1. Plain, 2. Fraktur, 3. Fraktur Clean, 4. Fraktur Framed, 5. Circled, 6. Circled Clean, 7. Cursive, 8. Cursive Clean, 9. Cursive Framed, 10. Uppercase, 11. Greek, 12. Greek Clean, 13. Greek Framed, 14. Leetspeak, 15. Leetspeak Clean, 16. Symbol Mix, 17. Unicode Sans, 18. Enclosed Letters, 19. Closest Unicode, 20. Script, 21. Megamix

## Karaoke treatments (7)

1. Readable Solid, 2. Line Rainbow, 3. Word Rainbow, 4. Random Letter Color, 5. Hashed Word Color, 6. Megamix1, 7. Megamix2

## Progress-bar styles (25)

1. Progress 01, 2. Progress 02, 3. Progress 03, 4. Progress 04, 5. Progress 05, 6. Progress 06, 7. Progress 07, 8. Progress 08, 9. Progress 09, 10. Progress 10, 11. Progress 11, 12. Progress 12, 13. Progress 13, 14. Progress 14, 15. Progress 15, 16. Progress 16, 17. Progress 17, 18. Progress 18, 19. Progress 19, 20. Progress 20, 21. Progress 21, 22. Progress 22, 23. Progress 23, 24. Progress 24, 25. Progress 25

## Playback speeds (34)

1. 0.001×, 2. 0.01×, 3. 0.05×, 4. 0.1×, 5. 0.2×, 6. 0.3×, 7. 0.4×, 8. 0.5×, 9. 0.6×, 10. 0.7×, 11. 0.8×, 12. 0.9×, 13. 1×, 14. 1.1×, 15. 1.25×, 16. 1.5×, 17. 1.75×, 18. 2×, 19. 2.5×, 20. 3×, 21. 4×, 22. 5×, 23. 6×, 24. 7×, 25. 8×, 26. 9×, 27. 10×, 28. 12.5×, 29. 15×, 30. 20×, 31. 25×, 32. 30×, 33. 35×, 34. 40×

## Visualizer combination count

The independent visualizer axes yield **112,320,000** base combinations. Palette reversal doubles the directly visible variants to **224,640,000**.

# Screenshots and visual reference plates

These recovered plates are linked local assets, not repeated placeholders. Real-session captures come first; controlled/generated plates then isolate one rendering dimension at a time.

## Real sessions

### Real playback: multiple artwork tiles, metadata, and fine-grained progress.

![Real playback: multiple artwork tiles, metadata, and fine-grained progress.](images/real_multi_artwork_and_progress.png)

### Real playback: the spectrum expands into karaoke space when no lyric occupies it.

![Real playback: the spectrum expands into karaoke space when no lyric occupies it.](images/real_expanded_visualizer.png)

### Real playback: history-aware shuffle status beside live metadata.

![Real playback: history-aware shuffle status beside live metadata.](images/real_shuffle_status_and_metadata.png)

### Real playback: EmojiMaxx karaoke in the packed three-line treatment.

![Real playback: EmojiMaxx karaoke in the packed three-line treatment.](images/real_karaoke_emojimax.png)

### Real playback: related artwork gallery and priority layout.

![Real playback: related artwork gallery and priority layout.](images/real_artwork_gallery.png)

## Controlled reference plates

### Generated reference: image-oriented SIXEL spectrum.

![Generated reference: image-oriented SIXEL spectrum.](images/sixel_spectrum_reference.png)

### Generated reference: the 25 visualizer glyph families.

![Generated reference: the 25 visualizer glyph families.](images/visualizer_glyph_families.svg)

### Generated reference: spectrum-shaping treatments under controlled input.

![Generated reference: spectrum-shaping treatments under controlled input.](images/visualizer_treatments.png)

### Generated reference: processing style and palette as independent axes.

![Generated reference: processing style and palette as independent axes.](images/processing_by_palette.png)

### Generated reference: all 32 palettes.

![Generated reference: all 32 palettes.](images/palettes_32.png)

### Generated reference: Signal Aurora family variants under one palette.

![Generated reference: Signal Aurora family variants under one palette.](images/signal_aurora_variants.png)

### Diagram: 30-Hz analysis interpolated into the adaptive high-rate paint pipeline.

![Diagram: 30-Hz analysis interpolated into the adaptive high-rate paint pipeline.](images/visualizer_pipeline.png)

### Diagram: the optional display-only frequency-axis warp.

![Diagram: the optional display-only frequency-axis warp.](images/frequency_axis_warp.png)

### Generated reference: twelve deterministic block-persistence behaviors.

![Generated reference: twelve deterministic block-persistence behaviors.](images/persistence_modes.png)

### Generated reference: display-only AGC before and after, with silence protected.

![Generated reference: display-only AGC before and after, with silence protected.](images/visual_agc_before_after.png)

### Generated reference: Twin DRCS, half-cell, and one-cell granularity.

![Generated reference: Twin DRCS, half-cell, and one-cell granularity.](images/visualizer_granularity_modes.png)

### Diagram: persistent queue rotation across invocations.

![Diagram: persistent queue rotation across invocations.](images/persistent_shuffle_queue.png)

### Generated reference: four independent fade/color-aging behaviors.

![Generated reference: four independent fade/color-aging behaviors.](images/fade_behaviors.png)

### Generated reference: 21 karaoke typography styles.

![Generated reference: 21 karaoke typography styles.](images/karaoke_typography_styles.png)

### Generated reference: seven karaoke color treatments using one pangram.

![Generated reference: seven karaoke color treatments using one pangram.](images/karaoke_color_treatments.png)

### Diagram: favorite lists versus one exact saved default.

![Diagram: favorite lists versus one exact saved default.](images/favorites_vs_defaults.png)

### Reference: compact color-grouped help overlay.

![Reference: compact color-grouped help overlay.](images/help_overlay.png)

### Reference: volume in the controls row without breaking progress geometry.

![Reference: volume in the controls row without breaking progress geometry.](images/volume_controls_layout.png)

### Diagram: compact header, number spacing, and visualizer row lock.

![Diagram: compact header, number spacing, and visualizer row lock.](images/header_spacing_and_row_lock.png)

### Diagram: history-aware shuffle construction.

![Diagram: history-aware shuffle construction.](images/history_aware_shuffle.png)

### Diagram: Winamp-compatible now-playing integration.

![Diagram: Winamp-compatible now-playing integration.](images/now_playing_integration.png)

### Generated reference: one-eighth-cell progress resolution.

![Generated reference: one-eighth-cell progress resolution.](images/progress_resolution.png)

### Diagram: synchronized, whole-frame visualizer painting.

![Diagram: synchronized, whole-frame visualizer painting.](images/atomic_visualizer_paint.png)

# One-line release history

Detailed evidence and rationale live in [`PAFPlayer_changelog.md`](PAFPlayer_changelog.md).

- **V1:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V2:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V3:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V4:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V5:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V6:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V7:** Refined the terminal UI and established regression coverage for the compact live player surface.
- **V8:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V9:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V10:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V11:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V12:** Separated Artist/Song animation, stabilized lyric-title ownership, EmojiMaxx fading, and real playlist visit history.
- **V13:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V14:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V15:** Made upcoming EmojiMaxx immediate and added OSC-8 clickable URLs without breaking terminal-cell width.
- **V16:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V17:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V18:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V19:** Documented real artwork, karaoke, visualizer, metadata, shuffle, fade, and progress behavior with reference plates.
- **V20:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V21:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V22:** Expanded the visual reference set for SIXEL, glyph families, and karaoke treatments.
- **V23:** Established the lower-rate visualizer presentation baseline later used to diagnose high-rate tearing.
- **V24:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V25:** Added bounded persistence modes, correct analyzer-behind behavior, physical top-row crop, robust SRT parsing, and EmojiMaxx refinements.
- **V26:** Added display-only AGC, exact-stem sidecar editing, verified history upserts, persistent queue rotation, and three granularity modes.
- **V27:** Moved shuffle-cache writes off track handoff, made terminal geometry focus-safe, and refined EmojiMaxx vocabulary.
- **V28:** Locked visualizer rows to column one and normalized circled-number spacing around the compact Play header.
- **V29:** Separated glyph treatment, processing, palette, persistence, fade, and granularity; added Signal Aurora variants and adaptive high-rate painting.
- **V30:** Made multi-row visualizer paints atomic with synchronized output and explicit row advances.
- **V31:** Corrected compact Help keys, history wording, and top-visualizer crop defaults.
- **V32:** Added hierarchical/permanent attribute rules, extended timed-lyric formats, and verified embedded lyric round-trips.
- **V33:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V34:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V35:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V36:** Preferred written-word EmojiMaxx mappings and added renderer diagnostics that remove window-sensitive terminal sequences.
- **V37:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V38:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V39:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V40:** Made large playlist loading report progress in five-percent steps.
- **V41:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V42:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V43:** Deferred filesystem checks for huge playlists and made lexical path identity independent of file existence.
- **V44:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V45:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V46:** Expanded theory diagnostics, ordered help output, and trimmed unused bottom terminal reservation.
- **V47:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V48:** Extended theory-mode range and architecture diagnostics for visualizer/process investigation.
- **V49:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V50:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V51:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V52:** Standardized analyzer launch/logging state and prevented shuffle from selecting the current physical track.
- **V53:** Prevented forward history repeats and made missing attrib.lst creation safe and non-destructive.
- **V54:** Established learned/scrobble hotkeys, standard attrib.lst creation, EmojiMaxx aliases, and clean Done/scrollback behavior.
- **V55:** Made learned writes contain only the explicit learned rule and report the exact written result.
- **V56:** Limited ordinary Last.fm submission to one scrobble per logical visit with explicit duplicate confirmation.
- **V57:** Added embedded-cover extraction/materialization when no usable sidecar cover exists.
- **V58:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V59:** Separated Last.fm Now Playing from earned scrobbling and serialized the per-visit network lifecycle.
- **V60:** Preferred the canonical C:\bat history database and added karaoke/visualizer compositing plus EmojiMaxx and learned-record refinements.
- **V61:** Made visualizer modes genuinely distinct and preserved exact legacy per-column geometry.
- **V62:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V63:** Captured resume successors before queue rotation and rejected physical aliases during resumed forward navigation.
- **V64:** Aligned semantic metadata columns by label rather than arbitrary string position.
- **V65:** Made narrow HUD layouts relax alignment before wasting additional terminal rows.
- **V66:** Implemented four karaoke/visualizer compositing modes and corrected expansion/genre behavior.
- **V67:** Added compound timed-lyric selection/parsing, asynchronous history startup, and corrected the Up-arrow vocabulary.
- **V68:** Greatly expanded usage examples and moved keystroke guidance next to playback options.
- **V69:** Made learned selectors durable across one/two-digit track prefixes and standardized record separators.
- **V70:** Made lyric-corpus tooling preserve written output through editor failures and avoid dumping generated code to stdout.
- **V71:** Aligned Last play under Album even when optional Comment consumes a competing row.
- **V72:** Introduced the persistent external album-art window, monitor-safe geometry, and Alt+A control contract.
- **V73:** Added aspect-aware art resizing, mouse controls, stable origin, playlist counts, and terminal glyph-spacing fixes.
- **V74:** Made the Tk artwork thread own shutdown and close cleanly even when the GUI never fully started.
- **V75:** Added colorful, sorted playlist-history reporting and its usage-level diagnostic.
- **V76:** Added the full-path playlist-analysis table, paging, ANSI-free export, and editor handoff.
- **V77:** Added separate progress reporting for history resolution and playlist-analysis generation.
- **V78:** Preserved history order through rebuilds, promoted the current track safely, and prevented removed tracks from reappearing.
- **V79:** No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.
- **V80:** Finalized physically exact two-line learned records and clean selector character classes.
- **V81:** Restored persistence bindings and built a numbered URL chooser with All/None/Escape handling.
- **V82:** Added full playback-time ReplayGain, unified URL controls, Help on F1, and an exact defaults manager.
- **V83:** Added learned extra-tag/removal workflows, robust playlist mutation, art foreground/border behavior, URL errors, and stable Dir rows.
- **V84:** Made nearly all modifier-heavy controls focus-only while retaining only deliberately global physical controls.
- **V85:** Improved editor focus handoff, inherited-learned detection, duplicate avoidance, and automatic attrib editor opening.
- **V86:** Added fast playlist INS/DEL/browser editing, idle art, hard redraw/reflow cleanup, catalog search, and extensive HUD/help polish.
- **V87:** Deduplicated physical path aliases, added the idle artwork gallery/weighted crossfades, and removed filesystem work from playlist browsing.
- **V88:** Added the raw-tag browser, collection aliases, inherited attrib editing, dense Dir/HUD semantics, and 30-second typed-tag idle behavior.
- **V89:** Hardened next-track distinctness, strict metadata grids, learned-input commit rules, and dense three-field rows.
- **V90:** Made Dir conditional on Play-line fit and restored the localhost web server and clean editor activation.
- **V91:** Added near-EOF resume safety, multidisc learned selectors, bounded three-hour shuffle avoidance, and branch-audit sentinels.
- **V92:** Eliminated duplicate metadata rows, unified layout timing, cleared repaint rows, refined learned timing, and corrected EmojiMaxx low.
- **V93:** Added Ctrl+O clean playlist relaunch, VLC art fallback, compact Last play, denser metadata, and faster Artist/Song throbs.
- **V94:** Fixed an immediate web-enabled playback crash caused by publishing before the loop timestamp existed.
- **V95:** Expanded the web controller with real transport/settings, clickable progress, live analyzer data, large rainbow lyrics, and exact Never display.
- **V96:** Unified native/web related artwork and mouse behavior, clickable metadata URLs, taskbar acknowledgement, and colon-safe HUD alignment.
- **V97:** Fixed WAV sample-rate timing, enforced MISC exact-stem art, added explicit cover downloads/global base attributes, and refined HUD/history/art behavior.
- **V98:** Intentionally skipped; no V98 release was issued.
- **V99:** Intentionally skipped; no V99 release was issued.
- **V100:** Made `=` reset volume to 100% and playback speed to 1× together.
- **V101:** Made art position/DPI ownership persistent, introduced the three-way lyric mode, and separated the web Choices scroller.
- **V102:** Added conventional artwork controls, native-size-until-resized behavior, and pointer-safe floating-lyric hit testing.
- **V103:** Made F5 art-safe, added independent floating-lyrics control, compact Last play packing, header track text, and aspect-fill art updates.
- **V104:** Isolated GUI lyric color animation from full artwork repainting and made empty floating state visibly diagnosable.
- **V105:** Replaced the fragile saved-cursor HUD anchor with absolute viewport rows and isolated lyric layers from cover rendering.
- **V106:** Separated artwork decode/lyric errors, added warning-ledger logging, dense metadata tails, foreground art toggle, and media-key modifiers.
- **V107:** Preindexed/cached INS search, kept visualizers live during prompts, made prompts blink, and cleaned Tk shutdown.
- **V108:** Added an immediate recent-visit shuffle ledger, removed stale cache history, and made Alt+3 human-oriented and one-row-per-tag.
- **V109:** Made Last play lookup pending-aware, wrote local history at 33%, coupled learned to history, and made Alt+3 live across tracks.
- **V110:** Split diagnostics into rotating errors/trace logs and fixed Tk lyric font ownership (`root=` instead of invalid `master=`).
- **V111:** Queued INS selections to play next, added global Ctrl+Alt+Up/Down volume, reset speed at session/playlist/insert boundaries, froze per-visit Last play, removed duplicate Dir reflow, restored illustrated docs, and made truncation close delimiters.
- **V112:** Made artwork geometry permanently user-owned with free resize, Ctrl-square constraint and black letterboxing; merged instrumental tag variants; reordered Help metadata; and added the optional three-row detail HUD.
- **V168:** Added a post-layout inline `Last play` colon-alignment pass, a source-configurable default, `Ctrl+Alt+I` toggle, `Ctrl+Alt+Shift+I` idle-art start, and four supplied-HUD regression fixtures.
