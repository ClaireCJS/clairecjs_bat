# 🎧 `play_audio_file.py` — the absurdly capable Windows-terminal audio player

> **Current documented build:** `2026-08-06-lyric-attribute-editing-v32`
>
> `play_audio_file.py` started life as a quick way to preview an audio file from the command line. It is now much closer to a tiny terminal-native media player: FFplay audio playback, persistent settings, playlist/history-aware shuffle, album-art galleries, two visualizer systems, timed karaoke, semantic EmojiMaxx lyrics, animated metadata, Last.fm scrobbling/history reports, OSC-8 clickable URLs, Winamp coexistence, Winamp-compatible now-playing TXT/JPG files, surround-output controls, and a frankly unreasonable amount of attention to terminal-cell geometry.

## Quick summary

If you only want to know why this program is fun:

- **Play almost anything FFmpeg can decode**: MP3, FLAC, WAV, AAC, ALAC, Ogg, Opus, WMA, Monkey's Audio, WavPack, DSD formats, and more.
- **Use it interactively**: pause, seek by several step sizes, change tracks/folders, alter speed from `0.001×` to `40×`, change volume up to 400%, pan left/right, switch stereo/5.1/7.1 output, loop, autoplay, and shuffle without restarting the script.
- **Trim dead air non-destructively at playback time**: sustained edge audio below **−43 dBFS** can be skipped while keeping an 80 ms safety pad; the source file and internal lyric/history timeline remain untouched.
- **Show album art and image-based spectrum graphics directly in the terminal with SIXEL/Chafa**, including up to 16 relevant images in a 4×4 gallery, intelligently prioritized and visually deduplicated. The documented image renderer is [Chafa 1.18.2](https://github.com/hpjansson/chafa/releases/tag/1.18.2).
- **🚩 Experiment with the DRCS soft-font spectrum visualizer** — *doesn’t work for the developer, but might work for you* — whose appearance model is now properly factored into **25 glyph families × 15 treatments × 65 processing styles × 32 independent palettes × 4 fade/color-aging behaviors × 12 block-persistence behaviors × 3 granularity modes = 112,320,000 discrete combinations**. Independent palette reversal doubles that to **224,640,000 visible direction variants** before continuous dimensions such as terminal width, audio, fade time, AGC and the frequency-axis warp are even counted. V29–V32 target a **120-Hz spectrum paint loop**, using 30-Hz FFT analysis plus interpolation and adaptive fallback when the terminal cannot keep up.
- **Paint high-rate visualizer frames atomically instead of row-by-row:** V30 wraps each complete spectrum repaint in DEC synchronized-output mode and advances between rows with explicit cursor-down + column-1 commands. This is specifically meant to eliminate the horizontal frame-age banding/tearing that can appear when a 120-Hz renderer updates a multi-row terminal visualizer faster than the terminal can present those rows as one coherent frame. Terminals that do not understand synchronized-output mode simply ignore that private mode.
- **Keep quiet music visually alive with adaptive visual normalization (AGC)**: spectrum amplitudes are normalized for display only, with a silence/noise gate and gain ceiling. The audio itself is never changed.
- **Run karaoke in the terminal** with SRT-first timing, LRC fallback, embedded/plain-text fallback, double-height DEC terminal text, animated line transitions, multiple typography/treatment modes, rainbow effects, and EmojiMaxx semantic substitutions.
- **Turn lyrics into the Windows Terminal tab/title marquee** while they are sung; song metadata returns automatically when there is a real lyric gap.
- **Animate Artist and Song metadata independently** through rainbow brightness cycles while leaving filenames/paths stable and readable.
- **Shuffle playlists using a database of when each track was actually played — then keep that shuffle as a persistent queue.** “Random” is intentionally *history-biased*: never-heard material and music you have not heard for a long time are pulled forward, with randomness inside age buckets. Once built, shuffle mode walks that queue **sequentially**. When a track is departed, it is moved to the tail immediately in memory and the newest queue snapshot is written asynchronously shortly afterward, so restarting the player continues with the next queued song instead of picking the same recent song again without making track handoff wait on JSON I/O. `Ctrl+Alt+R` deliberately throws that queue away and rebuilds it from history.
- **Remember where you were** in a playlist and resume the interrupted track/position when that track still exists in the new playlist.
- **Feed the same now-playing ecosystem as Winamp, with compatibility with Winamp’s now-playing plugin**: if `C:\mp3\lists` exists, the player writes `winamp_now_playing.txt` and `winamp_now_playing.jpg` there using the field-oriented layout documented for [WinampNowPlayingToFile](https://github.com/Aldaviva/WinampNowPlayingToFile); otherwise it stays portable and writes `play_audio_file-now-playing.dat/.jpg` beside the script.
- **Scrobble to Last.fm** after enough of a song has genuinely been heard, even when seeking; force a scrobble with a key; parse archived Last.fm logs into a local play-history database/report.
- **Repair ugly metadata situations**: read standard FFprobe tags, recover selected malformed ID3 text, and fall back to a cleaned filename for a missing song title without inventing Artist/Album data.
- **Make URLs useful**: display the real URL tag first, discover distinct URLs in comments, emit OSC-8 clickable hyperlinks in compatible terminals, and open the primary URL with `Ctrl+U` or browse all distinct URLs with `Ctrl+B`.
- **Play nicely with Winamp**: detect a running Winamp, pause it while this player owns the speakers, and resume it only when appropriate.
- **Persist visual/player settings and favorites** in the Windows registry, while keeping transient shuffle caches in `%TEMP%`. V29 distinguishes **favorites** (lists you can cycle) from **F1 defaults** (one exact saved configuration per dimension, set with `*`).

This is not merely an `ffplay` command wrapper. FFplay is the audio engine; `play_audio_file.py` is the state machine, UI renderer, metadata/lyrics/artwork system, playlist engine, history layer, and keyboard controller around it.

---


## ✏️🏷️ V32: aligned metadata, verified lyric editing, and live playlist attributes

V32 tightens three parts of the player that are easy to notice during daily use: the metadata grid, the lyric-edit round trip, and Claire's `attrib.lst` playlist attributes.

### Metadata is now a real three-column grid

The normal metadata rows no longer pack each line independently and then hope their labels happen to land in the same place. The first two rows use semantic columns:

- **Artist / Year** share the first colon stop;
- **Song / Genre** share the second colon stop; and
- **Album / URL** share the third colon stop.

For example, this layout keeps all three label columns vertically aligned in terminal-cell coordinates:

```text
   Artist: They Might Be Giants    Song: The Edison Museum      Album: No!
     Year: 2002                   Genre: Alternative              URL: http://www.tmbg.com/
```

The packer still falls back to wrapped single-field rows on genuinely narrow terminals rather than allowing an implicit terminal word-wrap. `Last heard:` remains opportunistic: it is appended to an existing row when it fits and gets its own row only when necessary.

### `Ctrl+E` is now an edit → `D` → verify workflow

Press **`Ctrl+E`** while playing or paused. PAFplayer finds every existing exact-stem text/lyric/subtitle sidecar it recognizes (including `.txt`, `.srt`, `.lrc`, `.vtt`, `.ass`, `.ssa`, `.sbv`, `.sub`, `.ttml`, `.dfxp`, and `.usf`) and opens them with the **executable behind Windows' current `.TXT` open association**. This deliberately lets an `.srt` or `.lrc` open in the same editor you chose for ordinary text files instead of relying on that extension's unrelated Windows association.

PAFplayer stays running and leaves a persistent **`press D when done`** notice in the controls row. When you press **`D`**:

1. the edited sidecars are read again as fresh lyric input;
2. plain lyric text is written back into the audio file's embedded plain-lyrics tag;
3. the preferred timed sidecar is written into PAFplayer's embedded timed-lyrics tag together with its format marker;
4. the tags are **read back from the file** and normalized values are compared with what was written;
5. only after that verification succeeds are lyrics reparsed and the live player refreshed; and
6. if playback had to release the audio file for tag writing, it resumes at the same playback position.

![V32 lyric edit and verification round trip](images/v32_lyric_edit_roundtrip.png)

Embedded write-back uses Python **Mutagen**. If the tag write or read-back verification fails, PAFplayer puts a conspicuous error on screen and appends the failure to:

```text
C:\logs\PAFPlayer\errors.log
```

That error-log location is also printed by `--usage`.

### `Ctrl+A` / `Ctrl+Alt+A`: edit the playlist-attribute rules

`A` by itself still toggles autoplay. The new modified bindings are separate:

- **`Ctrl+A`** — open the current track folder's `attrib.lst`, if present;
- **`Ctrl+Alt+A`** — open the current folder's `attrib.lst` plus every existing `attrib.lst` in its parent chain;
- **`D`** — finish the edit and request a fresh background attribute evaluation.

These files are part of the playlist system driven by:

```bat
generate-filelists-by-attribute.pl -g -igenerate-filelists-by-attribute-audio.ini
```

Source references: [`generate-filelists-by-attribute.pl`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/generate-filelists-by-attribute.pl) and [`generate-filelists-by-attribute-audio.ini`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/generate-filelists-by-attribute-audio.ini).

### Attribute rule semantics reproduced inside PAFplayer

Each applicable `attrib.lst` line is `<regex>:attr1,attr2,...` (the generator also accepts `::`, which is useful when a Windows drive colon occurs in the regex). PAFplayer evaluates existing parent `attrib.lst` files **from broadest/root-most to the track's own folder**, so local rules naturally come later. Regex matching is case-insensitive and is tested against forward-slash forms of the path, consistent with the generator's own format.

The assignment prefixes follow the playlist generator's permanence behavior:

| Prefix | Meaning | Can later ordinary rules undo it? |
|---|---|---|
| none | add | yes |
| `+` or `++` | strong add / whitelist | **no ordinary `-` removal** |
| `-` | remove | yes; it cannot defeat a whitelist |
| `--` | permanent blacklist | **no later add, `+`, or `++` restores it** |

So this sequence:

```text
dog,+animal,-animal,cat,--cat,cat
```

finishes with **`dog` and `animal` active**. `animal` survives because `+animal` whitelisted it; `cat` remains absent because `--cat` permanently blacklisted it before the final attempted add.

![V32 parent attrib.lst precedence](images/v32_attribute_resolution.png)

### `attrib.lst` versus generated `attributes.dat`

PAFplayer supports both sources. The exact source-code switch is:

```python
GET_ATTRIBUTES_FROM_ATTRIBUTESDAT_FILE_INSTEAD_OF_ATTRIBLIST_FILE = 0
```

`0` (the V32 default) walks only the handful of parent `attrib.lst` files relevant to the current song. `1` instead looks for `\mp3\lists\attributes.dat` (also respecting the `MP3` environment variable / current audio drive) and scans the generator's parseable `attribute:filename:value` records, treating positive values as active.

The default was chosen after a synthetic comparison of the two algorithms: a six-level parent tree containing **480 total rules** took about **1.9 ms median**, while scanning a **100,001-line `attributes.dat`** took about **33.4 ms median** on the development environment — roughly **17× slower**. This is an algorithm/path-size comparison, not a claim about the exact timing of Claire's current disks.

Attribute work is intentionally the **last startup job**. It begins only after playback, spectrum analysis, and the initial SIXEL work are underway, waits another two seconds by default, and its Windows worker thread is set to `THREAD_PRIORITY_LOWEST`. The `?` help page never waits for it: it shows `Attributes: loading quietly in background…` until ready, then displays the resulting attributes in their own final section.

---

## ❔ V31: richer live help, restored `V`, and human-date listening history

V31 turns the live `?` panel into a real **PAFplayer** status/help screen instead of only a key dump.  Its first rows now show **`PAFplayer V31`**, the current song, the active playlist path, and the previous-listen date for this song.  Pressing `?` once opens help for the normal short interval; **pressing `?` again while help is already visible adds 15 seconds**.  Key-repeat is debounced so holding the key does not accidentally add minutes at a time.  Holding `?` still prevents the panel from disappearing under your finger.

The sections are now separated by full-width divider rules.  Within each section, every key is given its own nearby hue variation while remaining inside that section's color family; descriptions remain deliberately dimmer.  This keeps the category-level color cue while making adjacent shortcuts easier to distinguish.

Visualizer keyboard cleanup in V31:

- `V` — next visualizer mode;
- `Shift+V` — previous visualizer mode;
- `Ctrl+Alt+D` — toggle the DRCS visualizer (the old `Ctrl+V` binding is retired);
- `W` — toggle SIXEL as before; and
- the source/CLI default for hidden top spectrum rows changes from **2 to 1** (`TRUNCATE_TOP_VISUALIZER_LINES = 1`).

The live metadata `Last heard:` field is also changed from relative ages to compact calendar language intended to fit beside other metadata:

```text
Last heard: Tuesday      # heard within the last week
Last heard: Aug 21       # older, but in the current year
Last heard: Oct 21 ’21   # a previous year
```

Because the value is shorter and more immediately recognizable than `1.1yr`/`6mos`, the normal metadata packer has a better chance of keeping it on an existing row rather than creating another line.

![V31 live help layout](images/v31_help_overlay.png)

## 🧱 V30: synchronized visualizer painting — restoring V23-like frame stability at 120 Hz

V23 painted the DRCS visualizer slowly enough that Windows Terminal usually finished presenting one multi-row spectrum before the next one arrived. V29 intentionally raised the possible repaint rate to 120 Hz. That improved motion, but it also exposed a terminal-presentation problem: a terminal can display the upper rows of frame *N+1* while the lower rows still belong to frame *N*. The result looks like horizontal banding, tearing, or a row that seems visually disconnected from the bars above and below it even when the underlying spectrum data is perfectly continuous.

V30 changes the **paint path only**. Audio analysis, AGC, interpolation, processing styles, palettes, persistence and granularity are unchanged. The visualizer now:

1. builds the complete multi-row frame in memory;
2. begins DEC private synchronized-output mode (`CSI ? 2026 h`);
3. moves to the visualizer origin;
4. paints each row with autowrap suppressed;
5. moves between rows with explicit **cursor-down (`CSI 1 B`) + absolute column 1 (`CSI 1 G`)** instead of relying on CR/LF/newline behavior at full terminal width; and
6. ends synchronized-output mode (`CSI ? 2026 l`) so supporting terminals present the buffered repaint as one coherent visual frame.

This deliberately addresses a class of glitches that cannot be fixed by changing FFT values: the spectrum can be numerically correct while the terminal still exposes different rows from different repaint generations.

![V30 synchronized visualizer paint](images/v30_visualizer_atomic_paint.png)

Two source-level switches document the behavior:

```python
VISUALIZER_SYNCHRONIZED_OUTPUT = 1
VISUALIZER_USE_CUD_ROW_ADVANCE = 1
```

If a terminal does not implement private mode 2026, it should ignore it; the explicit row positioning still remains useful.

## Screenshots and visual reference plates

The documentation intentionally uses **many different images** rather than recycling one attractive screenshot. The first group is from real player sessions during development; the second group is generated directly from the V26/V27/V28 algorithms where those controls changed; unchanged feature plates are retained from the build that introduced them so each control family can be compared under consistent input.

### Real sessions

#### Multi-artwork playback, metadata and fine-grained progress

![Real playback with multiple artwork and progress](images/v19_real_multi_artwork_and_progress.png)

#### Visualizer expanded upward when karaoke has nothing to say

![Real expanded visualizer](images/v19_real_expanded_visualizer.png)

#### History-aware shuffle status beside live metadata

![Real shuffle status and metadata](images/v19_real_shuffle_status_and_metadata.png)

#### EmojiMaxx karaoke in the packed three-line layout

![Real karaoke and EmojiMaxx](images/v19_real_karaoke_emojimax.png)

#### Five-image artwork case with priority rows visible

![Real artwork gallery](images/v19_real_artwork_gallery.png)

### Generated reference plates

These are deliberately controlled demonstrations rather than claims that one specific song will produce the exact same shape. They use the player's current palettes/transforms so you can compare one dimension at a time.

#### SIXEL graphics path

A recognizable square album-art example makes the raster behavior easier to understand than an abstract placeholder. **Metallica — _Master of Puppets_** is used here as the reference artwork: [open the album-art example](https://upload.wikimedia.org/wikipedia/commons/b/b3/Metallica-Master_Of_Puppets-CD.jpg). The player preserves the artwork's aspect ratio and lets Chafa scale/encode it for the terminal rather than stretching it into terminal-cell proportions.

![Synthetic music-like SIXEL spectrum raster](images/v22_generated_sixel_spectrum.png)

The spectrum image above is a controlled documentation mockup shaped to resemble a plausible music spectrum rather than a literal screenshot of one particular song. The real raster is generated from FFmpeg analysis at playback time. The supported image path is documented first because it is the practical album-art/SIXEL route. The reference version used for this build is [Chafa 1.18.2](https://github.com/hpjansson/chafa/releases/tag/1.18.2).

#### 25 visualizer glyph families

![Visualizer glyph families](images/v22_generated_visualizer_glyph_families.svg)

#### 15 visualizer treatments

![Visualizer treatments](images/v19_generated_visualizer_treatments.png)

#### V29 processing-style × palette architecture

V29 stops pretending every visual decision is a “color style.” The visualizer now has two independent axes:

1. **Processing style** — *where* color phase comes from: quilt geometry, stripes, frequency position, instantaneous amplitude, attack/decay, local spectral contrast, Signal Aurora, and so on.
2. **Palette** — *which actual colors* are assigned to that phase.

This means **Tartan + Fire**, **Tartan + Ocean**, **Signal Aurora + Fire**, and **Signal Aurora + Full Rainbow** are four legitimate combinations rather than four unrelated hard-coded “colors.”

![V29 processing × palette grid](images/v29_processing_x_palette.png)

#### 32 independent palettes

![V29 palettes](images/v29_palettes_32.png)

`C` / `Shift+C` changes only the palette. `Alt+Shift+C` reverses only the palette direction. `Alt+C` cycles favorite palettes. The direct-entry window is now `01–32`, because processing styles have their own controls instead of wasting palette numbers.

#### Signal Aurora becomes a processing family

The original **Signal Aurora** was clearly signal-processing logic wearing a color-system label. V29 promotes it to the processing axis and adds three broader-spectrum variants. The plate below uses the **same signal and the same Full Rainbow palette** for all four, so the differences shown are genuinely processing differences.

![Signal Aurora variants](images/v29_signal_aurora_variants.png)

- **Signal Aurora** — the familiar frequency + energy + impact blend.
- **Signal Aurora Full Spectrum** — traverses much more of the palette range, so a full-spectrum palette actually gets exercised.
- **Signal Aurora Prism** — responds more strongly to local spectral contrast, crest factor and instantaneous level.
- **Signal Aurora Storm** — broad signal-driven phase with deterministic per-frequency turbulence; still optimized for the high-rate renderer.

#### 120-Hz visualizer pipeline

V29 separates **audio analysis rate** from **screen paint rate**. FFmpeg still performs the expensive spectrum analysis at **30 Hz** in low-priority rolling chunks. The player linearly interpolates between those analyzed frames and can paint intermediate spectrum states at up to **120 Hz**. This provides smoother motion without asking FFmpeg to perform four times as many FFT/filter passes.

![V29 120-Hz pipeline](images/v29_120hz_pipeline.png)

The 120-Hz figure is a **target, not a fabricated claim**. The renderer measures its own paint time and adapts down toward 30 Hz if Python or the terminal host cannot sustain the requested frame budget. Important V29 speed work includes cached spatial/quilt phase grids, cached palette LUTs, cached truecolor escape strings, cached twin-DRCS color blends, once-per-bin color work for row-independent signal processors, suppression of identical consecutive frames, and removal of an unnecessary per-frame clear-to-end-of-screen operation.

On this build’s development benchmark at **180 terminal columns, 20 visible spectrum rows, Twin DRCS**, the Python-side renderer for the default Signal Aurora path is comfortably faster than the 8.33 ms budget required for 120 Hz. Actual Windows Terminal throughput still matters, which is why the adaptive limiter remains mandatory.

#### Experimental frequency-axis warp

`Ctrl+Alt+F9` toggles a display-only remapping of frequency space. The left **55%** of the spectrum is untouched. The mapping then curves progressively so that source frequencies in roughly the upper **30%** occupy only the final **15%** of visual width. Nothing about the audio or FFT itself changes.

![V29 frequency-axis warp](images/v29_frequency_warp.png)

`Ctrl+Alt+F8` now owns the separate “visualizer rises into blank karaoke rows” toggle.

#### Twelve block-persistence behaviors

Persistence is a real selectable temporal axis. The V26 plate deliberately feeds **the same known sequence** to every mode — `hit → quiet → quiet → quiet → new hit → quiet` — then runs the real persistence function for six frames. This illustrates the programmatic intent rather than sampling unrelated random moments.

![Twelve V26 persistence modes with deterministic block progression](images/v26_persistence_programmatic_intent.png)

#### Adaptive spectrum normalization / AGC

The spectrum analyzer still measures real amplitudes, but V26 applies a **display-only adaptive gain** before persistence/color rendering. Quiet songs therefore use the available visual height instead of living as a nearly black strip at the bottom; true silence stays below the gate and is not inflated into fake activity.

![V26 quiet-spectrum AGC before and after](images/v26_agc_normalization_before_after.png)

#### Three implemented horizontal granularity modes

`Shift+F4` cycles `2× Twin DRCS` (default) → `2× Half Cells` → `1× Cells`. The selection is saved, appears in the `F` favorite menu as `G`, and can be made the exact F1 default with `*`, then `G`.

![V26 visualizer granularity modes](images/v26_visualizer_granularity_modes.png)

#### Persistent shuffled queue across invocations

Historical weighting is used when the queue is built; after that, shuffle playback is sequential through the stored queue. Departed songs rotate to the tail immediately.

![V26 persistent shuffled queue behavior](images/v26_persistent_shuffle_queue.png)

#### Four fade/color-aging behaviors

The four existing fade/color-aging modes remain independent of the twelve block-persistence modes. They decide how retained spectrum energy is colored/brightened as it ages, while persistence decides the **geometry/history of the bars themselves**.

![Four fade behaviors](images/v19_generated_fade_behaviors.png)

Together the discrete DRCS design space is now **25 × 15 × 65 × 32 × 4 × 12 × 3 = 112,320,000** combinations before palette reversal, or **224,640,000** visible direction variants when reversal is counted.

#### 21 karaoke typography styles

![Karaoke typography styles](images/v19_generated_karaoke_styles.png)

Font coverage varies by terminal/font. The V26 glyph-family sampler is SVG specifically so the browser can fall back through Cascadia Code, DejaVu Sans Mono, Noto Sans Symbols and other installed fonts; this prevents Braille/Dots rows from disappearing simply because one rasterization font lacks those code points. The Unicode table below remains authoritative.

#### Seven karaoke color treatments using one pangram

![Karaoke treatments](images/v22_generated_karaoke_treatments.png)

The comparison sentence is **“Sphinx of black quartz, judge my vow.”** — a compact pangram with more useful punctuation/letter variety than the usual quick-brown-fox sentence.

#### `?` help overlay hierarchy

![V31 help overlay](images/v31_help_overlay.png)

The accent `⫽` sits **between complete key explanations**. Each individual key now has its own adjacent hue inside the section theme, descriptions remain dimmer, and horizontal divider rules separate sections. The masthead also shows `PAFplayer V31`, the active playlist, current song, and `Last heard:` date. Pressing `?` again while the overlay is up adds 15 seconds.

#### Compact volume placement and uninterrupted progress row

![V26 volume in the controls row](images/v25_volume_controls_layout.png)

Volume is intentionally kept off the progress row and appears immediately before the karaoke `K:` state as one of four level icons plus a percentage: **`🔇 0%`**, **`🔈 1–39%`**, **`🔉 40–79%`**, or **`🔊 80%+`**. Changing volume repaints the controls row immediately; the elapsed/total clock and progress bar stay visually contiguous.

#### V28 compact Play header, circled-number spacing, and visualizer row lock

![V28 header, EmojiMaxx number spacing and row-lock summary](images/v28_header_numeric_spacing_and_row_lock.png)

The current-track header is now **`▶ Play:`** instead of `🔊 Playing:`. `▶` describes playback state rather than volume, `⏸` is used while paused, and shortening the label to `Play:` leaves more horizontal budget for aligned metadata.

#### How historical shuffle is assembled

![History-aware shuffle diagram](images/v19_generated_history_shuffle.png)

#### Winamp-compatible now-playing file integration

![Now-playing integration](images/v19_generated_nowplaying_integration.png)

#### ⅛-cell progress resolution

![Progress resolution](images/v19_generated_progress_resolution.png)

---

# Basic typical usage

## Play one file

```bat
play_audio_file.py "C:\mp3\Ween\Chocolate and Cheese\01 Take Me Away.flac"
```

For ordinary single-file playback, looping defaults on unless you explicitly use `--no-loop`.

The player will generally:

1. validate the file;
2. locate FFplay/FFprobe/FFmpeg as required;
3. read metadata and repair/fallback where reasonable;
4. discover album art and timed lyrics;
5. optionally pause a currently-playing Winamp session;
6. render pre-play artwork;
7. begin FFplay playback;
8. start spectrum analysis in the background when DRCS is enabled;
9. continuously repaint status, progress, metadata animation, karaoke, and visualizer rows;
10. periodically write now-playing metadata/artwork;
11. scrobble when the genuine listened ranges become eligible;
12. restore Winamp afterward if this player was the thing that paused it.

## Play a playlist

```powershell
play_audio_file.py --playlist "C:\mp3\lists\everything.m3u8"
```

Playlist shuffle is deliberately a **persistent queue**, not “pick another random index every time.” On a historical rebuild, the player consults the local play-history database, favors never-heard and long-unheard tracks, and randomizes within recency groups. It then writes that ordered queue under `%TEMP%\play_audio_file\shuffle_cache\`.

After the queue exists:

- shuffle mode walks it **sequentially**;
- when a track is departed, that track is moved to the **tail**;
- the in-memory queue rotates immediately; its disk cache is rewritten asynchronously on a single latest-wins worker after a short 0.75-second grace period, so JSON serialization/disk I/O cannot delay the next track;
- restarting therefore begins at the next queue head instead of rediscovering the song that just played;
- an explicit Stop still records a resume point, so a deliberately interrupted track can resume rather than being silently rotated away;
- queue rotations preserve the original cache-build timestamp, so playing music cannot postpone expiration forever;
- `Ctrl+Alt+R` deletes the prepared queue and starts a fresh history-biased rebuild without stopping the current song.

```powershell
play_audio_file.py --shuffle-expiration-in-hours=5 --playlist "C:\mp3\lists\everything.m3u8"
```

A changed playlist file invalidates the cache immediately regardless of age.

### V27 track-transition latency

Large shuffled playlists can produce multi-megabyte JSON cache files. V26 wrote that JSON synchronously after rotating a departed song, which could create an audible pause before the next FFplay process launched. V27 removes cache serialization from the handoff: queue rotation is immediate, the next track selection proceeds immediately, and a daemon writer saves the latest snapshot shortly afterward.

## Random file from one folder

```bat
play_audio_file.py --random-file "C:\mp3\incoming"
```

or, from the current directory:

```bat
play_audio_file.py --random-file
```

## Random downward directory walk

```bat
play_audio_file.py --random-file-recursive "T:\mp3"
```

This randomly chooses child directories downward until it reaches a leaf directory containing playable audio, then chooses a file there.

## Disable karaoke or album art for a clean playback session

```bat
play_audio_file.py --no-karaoke --no-album-art "C:\mp3\song.flac"
```

## Disable all visualizers

```bat
play_audio_file.py --no-visualizers "C:\mp3\song.flac"
```

---

# Less-common / power-user usage

## Tune metadata throb speeds per invocation

```bat
play_audio_file.py --artist-throb-seconds=2.4 --song-throb-seconds=3.2 "C:\mp3\song.mp3"
```

Artist and Song are deliberately independent. Artist is normally faster and is placed on the opposite portion of the rainbow cycle so the two fields do not simply pulse in lockstep.

## Change the animated-title cutoff

The historical spelling is intentionally retained as a supported option:

```bat
play_audio_file.py --marqee-animation-if-longer-than=20 "C:\mp3\song.mp3"
```

The correctly spelled alias is accepted too:

```bat
play_audio_file.py --marquee-animation-if-longer-than=30 "C:\mp3\song.mp3"
```

Text at or below the threshold stays static; longer text scrolls.

## Trim rarely-used visualizer bands

```bat
play_audio_file.py --truncate-top-visualizer-lines=1 "C:\mp3\song.flac"
```

This does not reserve fake blank terminal rows. It drops spectrum height/bands from the top of the visualizer logic so the visible DRCS region remains packed.

## Edit lyric/karaoke sidecars and verify embedded tag write-back

Press **`Ctrl+E`** while a track is playing or paused. Existing exact-stem lyric/subtitle sidecars are opened together using Windows' current `.TXT` editor association. PAFplayer leaves a persistent **`press D when done`** notice. `D` rereads the edited files, writes the plain/timed lyric payloads into embedded tags, reads those tags back to verify the update, reparses the lyrics, and refreshes the player. Missing sidecars are not fabricated. Verification failures are shown prominently and logged to `C:\logs\PAFPlayer\errors.log`.

## Force a fresh historical shuffle queue

Press **`Ctrl+Alt+R`** during playlist playback to delete the current prepared queue/cache and build a new one from the play-history database. The current song keeps playing while the familiar `[shuffling …]` progress runs in the normal transient-status slot.

## Target a high visualizer frame rate

```bat
play_audio_file.py --visualizer-target-fps=120 "C:\mp3\song.flac"
```

This requests a **120-Hz spectrum paint loop**, not a 120-Hz FFT. Spectrum analysis remains 30 Hz and is interpolated. The scheduler measures paint cost and automatically requests a lower rate when Python/Windows Terminal cannot stay inside the frame budget. Values are clamped to V29's supported adaptive range of 30–120 Hz.

## Mix processing styles and palettes independently

- **`Alt+F6` / `Alt+F7`** — processing style previous/next.
- **`C` / `Shift+C`** — palette next/previous.
- **`Alt+Shift+C`** — reverse palette direction.
- **`C`, then `?`** — browse palette swatches.

For example, select **Tartan** once and then cycle Fire, Ocean, Vaporwave and Jewel without changing the tartan geometry. Or leave **Full Rainbow** selected and move through the four Signal Aurora processors.

## Change visualizer horizontal granularity

Press **`Shift+F4`** to cycle `2× Twin DRCS` → `2× Half Cells` → `1× Cells`. The default is Twin DRCS and the selection is saved. `F`, then `G` manages granularity favorites; `*`, then `G` makes the current granularity the exact F1 default.

## Test the frequency-distribution curve

Press **`Ctrl+Alt+F9`** to toggle the experimental frequency warp. The low 55% of frequency space stays in the same location; the curve progressively allocates less horizontal space to the upper frequencies, with source 70–100% compressed into roughly the last 15% of display width. Toggle it while listening to decide whether the denser high-frequency end is preferable.

## Change block-persistence behavior while playing

V26 implements twelve distinct **block-history** behaviors. These are intentionally separate from the four fade/color-aging modes.

- `Ctrl+G` — next persistence behavior.
- `Ctrl+Shift+G` — previous persistence behavior.
- `Alt+G` — cycle favorite persistence behaviors.
- `Ctrl+Alt+G` — favorite/unfavorite the current persistence behavior.

The selected mode is shown on the controls row as `PsN:Name`, and a brighter temporary notice appears when it changes. The default is **Phosphor Glow**, chosen because it is the closest to the smooth pre-persistence visualizer feel.

`-f/--fade-time` still exists, but it controls legacy retained-energy brightness decay; it is not the selector for these twelve geometrical persistence modes.

## Suppress the default Winamp-compatible now-playing target but write somewhere else

```bat
play_audio_file.py --no-now-playing-sidecar --now-playing "D:\temp\current-track.txt" "C:\mp3\song.mp3"
```

The companion artwork is written using the same base path with a `.jpg` suffix.

## Generate and display Last.fm play history

```bat
play_audio_file.py --generate-play-history-from-lastfm-logs
play_audio_file.py --display-play-history
```

The generator searches the known Last.fm desktop-scrobbler locations and archived log directories, parses several historical log formats, deduplicates plays, and writes `lastfm_play_history.csv` beside the script. The display command produces the pretty artist/count/date-range report and uses forgiving artist canonicalization for report grouping.

## Test EmojiMaxx glyph rendering

```bat
play_audio_file.py --emoji-display-test
```

This prints the semantic substitution table with code points and terminal-cell widths, useful when a glyph or emoji behaves badly in a particular terminal/font.

## Confirm which script Windows is actually running

```bat
play_audio_file.py --version
```

or:

```bat
play_audio_file.py --which-script
```

Both print the build ID **and the resolved pathname of the executing script**, which is invaluable when `PATH` contains multiple copies.

---

# Complete command-line option reference

The parser accepts either separate values (`--fade-time 0.1`) or `=` forms for several numeric options where noted.

| Option | Meaning | Default / behavior |
|---|---|---|
| `-h`, `--help` | Show usage and exit. | No playback. |
| `-u`, `--usage` | Show usage and exit. | Same general purpose as help. |
| `--version` | Print build ID and resolved script path. | Exit immediately. |
| `--which-script` | Print build ID and resolved script path. | Alias-like diagnostic behavior. |
| `-t`, `--unit-tests` | Run embedded unit/regression tests. | No playback. |
| `-e`, `--emoji-display-test` | Print EmojiMaxx/Unicode substitution test. | No playback. |
| `-l`, `--loop` | Force looping on. | Single-file playback already loops by default unless explicitly overridden. |
| `-L`, `--no-loop` | Force looping off. | Useful for one-shot previews. |
| `-k`, `--karaoke` | Enable lyric display. | On. |
| `-K`, `--no-karaoke` | Disable lyric display. | — |
| `--trim-edge-silence` | Enable non-destructive playback-time trimming of sufficiently quiet audio only at the beginning/end of a track. | On. |
| `--no-trim-edge-silence` | Disable edge-silence trimming. | — |
| `--trim-silence-threshold-db DB` / `--trim-silence-threshold-db=DB` | Threshold below which sustained edge audio is treated as silence. | `-43` dBFS. |
| `--trim-silence-min-duration SECONDS` / `--trim-silence-min-duration=SECONDS` | Quiet audio must persist this long before it qualifies for trimming. | `0.35s`. |
| `--trim-silence-keep SECONDS` / `--trim-silence-keep=SECONDS` | Safety pad preserved around detected audible material so attacks/releases are not guillotined. | `0.08s`. |
| `-r`, `--random-file [directory]` | Choose a random supported audio file directly in one folder. | Uses CWD if no directory positional argument is supplied. |
| `-R`, `--random-file-recursive [directory]` | Randomly walk downward through directories, then choose audio in the leaf. | Uses CWD if omitted. |
| `-p FILE`, `--playlist FILE` | Play a local M3U/M3U8/PLS/XSPF playlist with internal shuffle/history preparation. | Playlist mode uses shuffle. |
| `--shuffle-expiration-in-hours HOURS` | Reuse a completed internal playlist shuffle until this age. | `5` hours. `<=0` effectively disables reuse. |
| `--shuffle-expiration-in-hours=HOURS` | Same as above. | — |
| `-b`, `--initial-blank-line` | Permit the normal leading blank line where applicable. | On. |
| `-B`, `--suppress-initial-blank-line` | Suppress that leading blank line. | — |
| `-v`, `--visualizers` | Enable both DRCS and SIXEL visualizers. | Depends on persisted/default settings. |
| `-V`, `--no-visualizers` | Disable both visualizers. | — |
| `-s`, `--sixel-visualizer` | Enable the SIXEL image-spectrum renderer. | Source default off. |
| `-S`, `--no-sixel-visualizer` | Disable SIXEL spectrum. | — |
| `-d`, `--drcs-visualizer` | Enable the experimental DRCS soft-font spectrum. | Source default on in this build; **🚩 experimental — doesn’t work for the developer, but might work for you**. |
| `-D`, `--no-drcs-visualizer` | Disable DRCS spectrum. | — |
| `-f SECONDS`, `--fade-time SECONDS` | Set spectrum persistence/decay time. | `0.08` seconds. |
| `--fade-time=SECONDS` | Same as above. | `0` disables persistence. |
| `-a`, `--album-art` | Enable pre-play album-art display. | On. |
| `-A`, `--no-album-art` | Disable pre-play artwork. | — |
| `--truncate-top-visualizer-lines N` | Hide N highest/rarest visualizer rows from terminal output while still analyzing the full spectrum; the hidden bands do not become blank reserved rows. | `1`. |
| `--truncate-top-visualizer-lines=N` | Same as above. | — |
| `--visualizer-target-fps FPS` / `--visualizer-target-fps=FPS` | Requested high-rate spectrum paint target. FFT analysis remains 30 Hz and frames are interpolated; the paint loop adapts downward if the terminal cannot sustain the request. | `120` Hz, clamped to the supported 30–120 Hz adaptive range. |
| `--genre-emoji` | Enable genre-specific emoji next to Genre. | On. |
| `--no-genre-emoji` | Suppress genre emoji. | — |
| `--marqee-animation-if-longer-than N` | Animate the window-title marquee only above N display characters/cells. | `20`. Historical misspelling retained intentionally. |
| `--marqee-animation-if-longer-than=N` | Same as above. | — |
| `--marquee-animation-if-longer-than N` | Correct-spelling alias. | — |
| `--marquee-animation-if-longer-than=N` | Correct-spelling alias with `=`. | — |
| `--song-throb-seconds SECONDS` | Song metadata brightness-throb period. | About `3.18s`. |
| `--song-throb-seconds=SECONDS` | Same as above. | — |
| `--artist-throb-seconds SECONDS` | Artist metadata throb period. | About 33% faster than Song. |
| `--artist-throb-seconds=SECONDS` | Same as above. | — |
| `--shuffle-throb-seconds SECONDS` | Active `[shuffling …]` brightness-throb period. | Faster than normal metadata and also uses ANSI blink. |
| `--shuffle-throb-seconds=SECONDS` | Same as above. | — |
| `-n`, `--no-now-playing` | Disable all now-playing TXT/DAT and JPG output. | Output enabled. |
| `-N`, `--no-now-playing-sidecar` | Suppress the automatically chosen now-playing target while still permitting `--now-playing`. | Uses `C:\mp3\lists\winamp_now_playing.txt/.jpg` **only if that directory exists**; otherwise uses script-side `play_audio_file-now-playing.dat/.jpg`. |
| `-o PATH`, `--now-playing PATH` | Additionally write now-playing data to PATH and artwork to the same base name with `.jpg`. | Optional extra target. |
| `-ghfl`, `--generate-play-history-from-lastfm-logs` | Parse Last.fm/Audioscrobbler logs and write `lastfm_play_history.csv`. | Early exit. |
| `-dh`, `--display-play-history` | Display the pretty play-history report from the generated CSV. | Early exit. |
| `AUDIOFILE` | Positional audio filename. | Required for ordinary playback. |

### Command-line validation

The script rejects negative fade times, negative marquee thresholds, invalid shuffle-cache ages, non-finite silence thresholds, non-positive silence-duration requirements, negative silence safety pads, and invalid/non-numeric values where numeric options are expected. Unknown `-` options are errors rather than silently becoming filenames.

---

# Keyboard controls — complete reference

Press `?` during playback for the compact live map. **Press `?` again while it is visible to add 15 seconds.** Esc closes that overlay/menu but does not stop playback.

The first two help rows identify **PAFplayer V31**, the current song, active playlist, and when this song was last heard. The live map is color-grouped without wasting rows on category headings: every **individual keystroke gets a slightly different adjacent hue** within its section theme, `⫽` remains a calmer separator, descriptions are dimmest, and full-width divider rules separate sections.

## Playback / transport

| Key | Action |
|---|---|
| `Space` / `Pause` / media Play-Pause | Pause/resume. |
| `X`, `Q`, `Ctrl+W`, `Ctrl+C`, `Alt+F4` | Stop/exit playback. Esc deliberately does **not** stop. |
| `Left` / `Right` | Seek −/+5 seconds. |
| `Shift+Left` / `Shift+Right` | Seek −/+15 seconds. |
| `Ctrl+Left` / `Ctrl+Right` | Seek −/+60 seconds. |
| media Previous / Next | Seek −/+10 seconds rather than changing playlist tracks. |
| `+` / `-` | Increase/decrease playback speed through the predefined speed ladder. |
| `2` / `5` / `7` | Stereo / 5.1 / 7.1 output expansion. |
| `L` | Toggle looping. |
| `Up` / `Down` | Volume ±5%. Holding accelerates repeated changes; the `🔇/🔈/🔉/🔊 N%` state repaints immediately. |
| `Shift+Up` / `Shift+Down` | Volume ±20%. |
| `=` | Reset volume to 100%. |
| numpad `4` / `6` | Balance left/right. |
| numpad `5` | Center balance. |

## Track / folder / playlist controls

| Key | Action |
|---|---|
| `<` / `>` | Previous/next track. In playlist mode, previous uses a real visit-history cursor so repeated `<` walks backward rather than bouncing between two tracks. |
| `{` / `}` | Previous/next directory containing audio. |
| `R` | Toggle shuffle. |
| `A` | Toggle autoplay; autoplay enables shuffle behavior. |
| `Ctrl+Alt+R` | Force a fresh history-biased rebuild of the shuffled queue/cache. |

## Karaoke / EmojiMaxx

| Key | Action |
|---|---|
| `Ctrl+E` | Edit existing exact-stem lyric/subtitle sidecars using Windows' `.TXT` handler; leaves a persistent `D`-to-finish prompt. |
| `D` | Finish pending lyric/attribute edits; lyric changes are written to embedded plain/timed tags and verified by readback. |
| `Ctrl+A` | Edit the current folder's `attrib.lst`. |
| `Ctrl+Alt+A` | Edit current + parent `attrib.lst` files; `D` refreshes attributes afterward. |
| `F4` | Toggle EmojiMaxx. |
| `F2` / `F3` | Previous/next karaoke style. |
| `Shift+K` / `K` | Aliases for karaoke style previous/next. |
| `Shift+F2` / `Shift+F3` | Previous/next karaoke treatment. |
| `Ctrl+K` | Next karaoke treatment. |
| `Alt+K` | Cycle saved karaoke favorites. |
| `Ctrl+Alt+K` | Toggle current karaoke favorite. |
| hold `F2+F3` ~3s | Karaoke style Megamix. |
| hold `Shift+F2+Shift+F3` ~3s/6s | Treatment Megamix1 / Megamix2. |

## Visualizer / processing / palette / favorites / defaults

V29 deliberately separates *geometry*, *signal processing* and *colors*. The keys follow that separation:

| Key | Action |
|---|---|
| `V` / `Shift+V` | Next / previous visualizer mode. This restores the original fast `V` navigation. |
| `Ctrl+Alt+D` | Toggle the DRCS visualizer. This replaces the retired `Ctrl+V` binding. |
| `F6` / `F7` | Previous / next **glyph family** within the current treatment. |
| `Shift+F6` / `Shift+F7` | Previous / next visualizer **treatment**. |
| `Alt+F6` / `Alt+F7` | Previous / next **processing style**. This is where Tartan, Plaid, Signal Aurora, Amplitude, Peak Proximity, etc. live. |
| `C` / `Shift+C` | Next / previous **palette**. Opens a 3-second direct-entry window. |
| digits during that window | Jump directly to palette `01–32`. Two digits commit immediately; a single digit commits when the window expires. |
| `C`, then `?` | Open the interactive palette catalog. Four palettes are shown per page; `Space` advances and `Esc` returns. |
| `Alt+Shift+C` | Reverse the current palette direction without changing processing. |
| `Alt+C` | Cycle favorite palettes. |
| `Shift+F4` | Cycle granularity: **2× Twin DRCS** → 2× Half Cells → 1× Cells. Twin DRCS remains the factory default. Granularity is both favoriteable and defaultable. |
| `Ctrl+G` / `Ctrl+Shift+G` | Next / previous block-persistence behavior. |
| `Alt+G` | Cycle favorite persistence modes. |
| `Ctrl+Alt+G` | Favorite/unfavorite the current persistence mode. |
| `Ctrl+Alt+F8` | Toggle the normal “visualizer expands into completely blank karaoke space” behavior. |
| `Ctrl+Alt+F9` | Toggle V29’s experimental frequency-axis warp. |
| `F` | **Favorite style/treatment/palette/etc** menu. Favorites are *lists* you may cycle through. |
| `*` | **Set F1 default(s)** menu. Defaults are *single exact values*, never lists and never cycles. |
| `F1` | Apply your saved defaults. If you never set a user default for a dimension, the factory default is used. |
| `Alt+F1` | Undo the most recent F1 reset. |

### `F` favorite submenu

`F` remains for collections of choices you like. Its current categories are:

- `V` — favorite visualizer glyph style
- `I` — favorite visualizer treatment/interpretation
- `S` — favorite processing style
- `C` — favorite palette
- `G` — favorite granularity
- `K` — favorite karaoke style
- `T` — favorite karaoke treatment
- `E` — favorite EmojiMaxx state
- `P` — favorite persistence behavior
- `R` — restore one favorite category
- `A` in Restore — restore all favorite categories
- `Esc` — abort/back

### `*` F1-default submenu

`*` looks similar because the same dimensions are useful, but its semantics are intentionally different. There is exactly **one default value per setting**. Pressing `*`, then a category stores the *current* value as what F1 should restore later:

- `V` / `I` — current glyph style / treatment
- `S` — current processing style
- `C` — current palette
- `G` — current granularity
- `K` / `T` — current karaoke style / treatment
- `E` — current EmojiMaxx state
- `P` — current persistence mode
- `W` — current frequency-warp state
- `A` — snapshot all supported current settings into the F1 default configuration
- `Esc` — cancel

![Favorites versus F1 defaults](images/v29_favorites_vs_defaults.png)

The live `?` map has been updated to make this distinction visible while adding divider rules rather than text category headings:

![V31 help overlay](images/v31_help_overlay.png)

## Progress bar

| Key | Action |
|---|---|
| `P` | Next progress-bar style. |
| `Shift+P` | Previous progress-bar style. |

The bar has **⅛-cell boundary resolution** using Unicode fractional block glyphs. The unplayed remainder is primarily background-color based, which avoids the black moat that appeared when the partial block and empty texture used incompatible cell backgrounds.

## Experimental / utility

| Key | Action |
|---|---|
| `Ctrl+Alt+F8` | Toggle the default “visualizer rises into blank karaoke rows” behavior. A `💹−` marker is shown only when the normally-on behavior has been disabled. |
| `Ctrl+Alt+F9` | Toggle the experimental global frequency-axis warp: low 55% unchanged, upper frequencies progressively compressed. |
| `Shift+F10` | Toggle karaoke-over-visualizer overlay. |
| `Ctrl+U` | **URL**: open the primary URL immediately. |
| `Ctrl+B` | **Browse** all distinct track URLs. If several exist, choose `1`, `2`, `3`, or `A` for all; **Esc aborts**. Multiple opens are separated by one second. |
| `Ctrl+Alt+L` | Force an immediate Last.fm scrobble attempt. |
| `*` | Set one or all single-valued F1 defaults from the current configuration. |
| `F1` | Apply saved user defaults over factory defaults. |
| `Alt+F1` | Undo the last reset-to-defaults operation. |
| `F5`, `Ctrl+L`, `Ctrl+R` | Redraw the UI. |
| `?` | Show the compact help overlay. Press `?` again while it is up to add **15 seconds**; holding it keeps the panel alive. |
| `Esc` | Close help/modal menu and restore playback UI; never exits normal playback. |

---

# Source-level configuration flags and tuning constants

Some behaviors are intentionally source-level knobs rather than command-line options. They sit near the top of `play_audio_file.py` so the “house style” of the player can be tuned once without growing the command line indefinitely.

## Now-playing / Winamp coexistence

| Constant | Current value | Purpose |
|---|---:|---|
| `WRITE_NOWPLAYING_THIS_OFTEN` | `5.0` | Seconds between periodic now-playing TXT/JPG refreshes while playing. |
| `PREVENT_WINAMP_PAUSE_WHEN_WE_ARE_PAUSED` | `0` | Controls special Winamp coexistence behavior around this player's paused state. |
| `NOW_PLAYING_SONG_INFO` | `C:\mp3\lists\winamp_now_playing.txt` | **Preferred** Windows metadata path only when `C:\mp3\lists` already exists; otherwise the script-side `play_audio_file-now-playing.dat` target is used. |
| `NOW_PLAYING_ART` | `C:\mp3\lists\winamp_now_playing.jpg` | Matching **preferred** artwork path when `C:\mp3\lists` exists; otherwise the script-side `play_audio_file-now-playing.jpg` target is used. |

## Karaoke timing / animation

| Constant | Current value | Purpose |
|---|---:|---|
| `LYRIC_FADE_SECONDS` | `6.0` | General fade tail for a lyric after its nominal timing. |
| `LYRIC_NEIGHBOR_MAX_BRIGHTNESS` | `0.66` | Maximum brightness of previous/next neighboring lyric bands. |
| `LYRIC_NEXT_FADE_MAX_SECONDS` | `6.0` | Maximum pre-roll fade duration for the upcoming line. |
| `LYRIC_PREVIOUS_FADE_MAX_SECONDS` | `6.0` | Maximum fade duration for the already-sung line. |
| `LYRIC_PREVIEW_LEAD_SECONDS` | `0.25` | Small lead offset used when previewing the next timed cue. |
| `LYRIC_SCROLL_ROW_STEPS` | `2` | Physical row travel for the packed three-band transition. The old four-row value belonged to a layout with blank rows between lyric bands. |
| `LYRIC_SCROLL_STEP_SECONDS` | `0.08` | Time per lyric-transition row step. |
| `HIDE_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT` | `25` | Threshold used only when incoming EmojiMaxx is configured to respect fade. |
| `HIDE_PREVIOUS_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT` | `50` | Already-sung line can revert from emoji to underlying words once it gets sufficiently dark. |
| `NEXT_SUNG_LINE_EMOJIMAXX_ON_AT_FIRST` | `1` | **Important asymmetry:** with `1`, the upcoming line is EmojiMaxxed from its first visible instant; the current sung line always keeps EmojiMaxx; only the fading, already-sung line is allowed to de-EmojiMaxx. Set `0` if you specifically want the incoming line to start as words and switch to emoji after the incoming threshold. |
| `LYRIC_MAX_UNTIMED_SECONDS` | `15.0` | Prevents an untimed cue from owning the screen forever when no explicit end exists. |

## Edge-silence trimming

| Constant | Current value | Purpose |
|---|---:|---|
| `TRIM_EDGE_SILENCE_ENABLED` | `1` | Master default for non-destructive beginning/end trimming. |
| `TRIM_EDGE_SILENCE_THRESHOLD_DB` | `-43.0` | Audio below this dBFS threshold can count as edge silence. |
| `TRIM_EDGE_SILENCE_MIN_DURATION_SECONDS` | `0.35` | Quiet edge audio must persist this long before trimming is allowed. |
| `TRIM_EDGE_SILENCE_KEEP_SECONDS` | `0.08` | Safety pad kept around detected audible material. |
| `TRIM_EDGE_SILENCE_SCAN_SECONDS` | `60.0` | Maximum amount of each edge inspected for trim boundaries. |

The first four also have the command-line controls documented above; the scan-window size remains a source-level tuning knob.

## Window-title marquee

| Constant | Current value | Purpose |
|---|---:|---|
| `TITLE_MARQUEE_CHARS_PER_SECOND` | `6.0` | Horizontal marquee speed. |
| `TITLE_MARQUEE_REFRESH_SECONDS` | `0.12` | Title repaint cadence. |
| `LYRIC_TITLE_RETURN_TO_SONG_GAP_SECONDS` | `3.0` | If the next lyric is farther away than this, the title returns to Artist/Song rather than holding stale karaoke text. |
| `TITLE_MARQUEE_WIDTH` | `54` | Internal title-window width used when slicing the scrolling ring. |

The activation threshold itself, `MARQUEE_ANIMATION_IF_LONGER_THAN`, also has a command-line override.

## Rainbow animation

| Constant | Purpose |
|---|---|
| `SONG_RAINBOW_CYCLE_SECONDS` | Full hue-cycle time for Song. |
| `SONG_RAINBOW_THROB_SECONDS` | Brightness pulse period; CLI-overridable. |
| `ARTIST_RAINBOW_THROB_SECONDS` | Independent Artist pulse, intentionally faster; CLI-overridable. |
| `SHUFFLE_RAINBOW_THROB_SECONDS` | Active shuffle-status pulse; CLI-overridable and additionally blinked. |
| `SHUFFLE_RAINBOW_CYCLE_SECONDS` | Hue-cycle timing for shuffle status. |

## Progress/status appearance

| Constant | Current value | Purpose |
|---|---:|---|
| `PROGRESS_EMPTY_BACKGROUND_BRIGHTNESS_BOOST` | `1.08` | Makes the unplayed tinted background slightly brighter so fractional boundaries remain visually continuous. |
| `PLAYING_PATH_RGB` | `(105, 235, 145)` | Bright green path/filename color. The filename itself does not throb. |

## Spectrum / visualizer defaults

V29’s spectrum path is intentionally split into a modest analysis cadence and a much faster terminal-paint cadence. These are the important source-level knobs:

| Constant | Default | Meaning |
|---|---:|---|
| `SPECTRUM_ANALYSIS_FPS` | `30` | FFmpeg/FFT analysis cadence. Analysis is intentionally *not* run at 120 Hz. |
| `VISUALIZER_TARGET_FPS` | `120.0` | Requested terminal spectrum paint target; also exposed as `--visualizer-target-fps`. |
| `VISUALIZER_MIN_ADAPTIVE_FPS` | `30.0` | Lower bound for the adaptive visualizer scheduler. |
| `VISUALIZER_MAX_ADAPTIVE_FPS` | `120.0` | V29’s supported high-rate ceiling. |
| `VISUALIZER_RENDER_UTILIZATION` | `0.72` | Maximum fraction of a frame budget the scheduler is willing to spend painting before requesting a lower rate. |
| `VISUALIZER_STATUS_FPS` | `30.0` | Slower clock/progress/karaoke UI cadence; text does not need 120-Hz repainting. |
| `VISUALIZER_IDLE_SLEEP_MAX` | `0.004` | Maximum main-loop nap while waiting for a visualizer deadline; removes the old 20-ms/50-Hz ceiling. |
| `DEFAULT_VISUALIZER_GRANULARITY` | `3` | `1` = 1× Cells, `2` = 2× Half Cells, `3` = **2× Twin DRCS**, the default. |
| `DEFAULT_FREQUENCY_WARP_ENABLED` | `0` | Factory state for the Ctrl+Alt+F9 frequency-distribution transform. |
| `VISUALIZER_DISABLE_AUTOWRAP_DURING_PAINT` | `1` | Disable terminal autowrap only while a spectrum frame is painted to avoid right-edge wrap-pending drift. |
| `VISUALIZER_FORCE_ROW_COLUMN_ONE` | `1` | Hard-anchor every spectrum row at terminal column 1. |
| `VISUALIZER_AGC_TARGET_PEAK` | `0.90` | Display-only normalization target. |
| `VISUALIZER_AGC_MIN_SIGNAL` | `0.025` | Silence/noise gate: do not amplify frames below this signal level. |
| `VISUALIZER_AGC_MAX_GAIN` | `5.0` | Maximum display-only gain. Audio itself is untouched. |
| `VISUALIZER_AGC_BOOST_SMOOTHING` | `0.30` | Gain rises gently when music is quiet. |
| `VISUALIZER_AGC_CUT_SMOOTHING` | `0.55` | Gain falls more quickly when loud material arrives. |
| `SPECTRUM_INITIAL_CHUNK_SECONDS` | `1.25` | Initial low-priority analysis chunk, kept small so the visualizer wakes quickly. |
| `SPECTRUM_BACKGROUND_CHUNK_SECONDS` | `3.0` | Rolling background chunk size. |
| `SPECTRUM_ANALYSIS_AHEAD_SECONDS` | `2.5` | Analyzer stays only slightly ahead of live playback rather than racing through the file. |
| `SPECTRUM_BACKGROUND_START_DELAY_SECONDS` | `0.35` | Brief startup grace period so audio/UI startup wins resource contention. |
| `DEFAULT_VISUALIZER_FADE_SECONDS` | `0.08` | Legacy retained-energy fade duration; CLI-overridable via `--fade-time`. |
| `TRUNCATE_TOP_VISUALIZER_LINES` | `2` | Analyze the top bands but never display the two rarely-hit highest visualizer rows. |

The high-rate path also uses cached processing grids, palette LUTs, truecolor escape strings, twin-color blends and duplicate-frame suppression. Those are implementation details rather than user-facing settings, but they are a major reason the default Signal Aurora path can fit inside a 120-Hz Python-side frame budget on the development benchmark.

## Album-art rendering

| Constant | Current value | Purpose |
|---|---:|---|
| `ALBUM_ART_PREVIEW_COLUMNS` | `4` | Maximum images across per gallery row. |
| `ALBUM_ART_PREVIEW_ROWS` | `4` | Maximum gallery rows. |
| `ALBUM_ART_PREVIEW_MAX_IMAGES` | `16` | Derived maximum gallery count. |
| `ALBUM_ART_DIVIDER_GUARD_PIXELS` | `2` | Tiny black guard **inside** the final SIXEL raster to prevent a few bottom pixels visually bleeding across a following text divider without paying for an entire blank terminal row. |
| `ALBUM_ART_IMAGE_EXTENSIONS` | JPG/JPEG/PNG/WebP/BMP/GIF/TIF/TIFF | Sidecar formats considered. |

## Playback speed ladder

`PLAYBACK_SPEEDS` is a source-level tuple ranging from **0.001×** through **40×**. `+` and `-` walk through these discrete values rather than applying an arbitrary continuous multiplier, so every step is predictable and persisted by index.

## Genre / EmojiMaxx dictionaries

The `semantic` and `SEMANTIC_PHRASES` maps are deliberately editable source data. They are not merely cosmetic lookup tables: phrase substitutions happen before individual-word substitutions so things like `one of → ❶ of` preserve intentional spacing and meaning. The current table also contains explicit custom choices such as:

```text
world  → 🌍
pirate → 🏴‍☠️
snake  → 🐍
snakes → 🐍🐍🐍
```


---

# What the player actually does — deep dive

## 1. Audio engine and process control

FFplay is used as the actual decoder/output process because it already supports an enormous range of audio formats and Windows audio devices. The Python program controls FFplay by starting/restarting it at calculated offsets when needed rather than pretending FFplay is a full remote-control API.

That architecture enables:

- seeking by restarting at the requested position;
- changing speed while keeping the current playback position coherent;
- changing output-channel configuration without abandoning the track;
- changing balance/volume with controlled process restarts where necessary;
- tracking the ranges that were genuinely listened to across seeks/restarts.

The player records listened segments and merges overlaps. That matters for scrobbling: repeatedly seeking backward cannot artificially make the same seconds count multiple times.

## 2. Metadata: normal first, repair only when needed

`probe_audio_metadata()` uses FFprobe for normal format/stream tags. That keeps the common path standards-based and format-agnostic.

The robustness layer then deals with files that are less cooperative:

- empty/missing standard fields remain empty rather than being invented;
- selected malformed ID3 text patterns can be recovered from raw frames;
- good FFprobe metadata always wins over recovery guesses;
- if Song/Title is still absent, a conventional leading track prefix is removed from the filename and the resulting stem can become the Song display;
- Artist and Album are **not fabricated** merely because a folder name looks plausible.

That philosophy is intentionally conservative: recover data when there is evidence; infer only the one field where the filename itself is a strong, user-visible fallback.

## 3. Metadata layout is width-aware rather than line-oriented

The header tries to use horizontal space intelligently:

- A compact state-aware `▶ Play: C:\long\path\song.flac (3m42s)` line is used when it fits; while paused the leading state glyph becomes `⏸`.
- If it does not fit, Folder and `Play:` can split without forcing terminal word wrap. The shorter label also makes colon alignment cheaper, so metadata can line up more often without causing a wrap.
- Artist and Song are high-priority metadata.
- Album and Year are packed next when possible.
- Genre comes before Comment whenever they share a row.
- URL is displayed when available.
- Comment values consisting only of `Cover (front)` are suppressed.
- A Comment URL duplicated by the real URL field is not redundantly shown as though it were additional information.
- V32 uses semantic column stops: **Artist/Year**, **Song/Genre**, and **Album/URL** share exact terminal-cell colon positions on the two main metadata rows.
- On narrow terminals, an oversized field moves to a clean wrapped line rather than shifting a later metadata label or triggering implicit terminal wrap.
- `Last heard:` is appended to an existing row when there is room and otherwise receives its own clean row.

Artist and Song receive independent rainbow animation. The path and filename deliberately remain stable bright green so the file location is always easy to read.

## 4. Window-title / tab marquee

The title bar has two personalities.

### Normal playback

It identifies the current song and can scroll when the display identity exceeds the configurable threshold.

### Active karaoke

Karaoke takes exclusive ownership of the title. No PID and no `— play_audio_file` suffix is appended while a lyric is being shown.

For long animated lyric titles, the microphone acts as a trailing delimiter so it does not repeatedly shove the visible text sideways at the beginning of every marquee cycle. Short/static karaoke text can use microphone framing.

When a cue actually ends, the player looks ahead. If another lyric is coming very soon, the lyric context stays in the title; if the gap is at least `LYRIC_TITLE_RETURN_TO_SONG_GAP_SECONDS`, normal Artist/Song identification returns.

## 5. Karaoke source precedence and timing

Timed lyric source order is intentionally:

1. **`.srt` sidecar** — preferred because each cue normally includes a start **and an explicit end timestamp**;
2. `.lrc` sidecar — useful, but usually start-only timing;
3. adjacent/plain-text lyric sources;
4. embedded FFprobe lyric tags.

Sidecar text decoding detects UTF-16 BOM/NUL patterns as well as UTF-8, because real-world SRT files are very often saved by Windows tools in UTF-16LE. The finder also compares sidecar stems with Unicode NFC normalization + case folding, and **SRT always beats LRC** because SRT supplies an explicit end time. Comment/header lines before cue 1 are tolerated. V25 was regression-tested against a Claire-generated SRT with those header comments.

The screen uses three logical lyric bands: previous, current, next. Double-height DEC rendering means each logical line consumes two physical terminal rows. The transition system is therefore based on the packed 0/1, 2/3, 4/5 geometry rather than the obsolete layout that once contained blank rows between bands.

### V26 karaoke visibility refinements

The upcoming line is deliberately capped at **80%** of full current-line brightness, so its fade-in occupies a lower visual range and the sung line remains dominant. The already-sung line uses its own dimmer fade path.

When karaoke owns the Windows tab/title, the microphone delimiter is **only at the end** (`lyric text 🎤`). Whether the title scrolls is decided from the stripped lyric itself — trailing spaces and the microphone do not push a short lyric over the marquee threshold.

## 6. EmojiMaxx

EmojiMaxx is a semantic layer **on top of** the selected karaoke typography style. It scans lyric words and selected phrases, substitutes useful emoji/Unicode symbols, and then lets the karaoke color treatment operate independently.

V27 removes the `alone` substitution entirely; the literal word **alone** now remains text.

The expanded dictionary was not built by throwing random English words at an emoji list. Its source comments document a deliberate vocabulary pass against the **COCA Top-5,000 frequency dataset (5,050 ranked part-of-speech rows)**, followed by matching against Unicode Emoji 17.0 names and Unicode 17.0 symbol names. The intent is practical coverage of words people actually sing, while avoiding replacements that are visually cute but semantically useless.

Phrase replacements are protected before word replacements, so multi-word ideas such as `thank you`, `my heart`, `on fire`, `one of`, and `fall in love` can behave as units. The system also deliberately uses circled numbers such as `❶` instead of keycap-number emoji in karaoke because those render much more reliably in DEC double-height text.

### Fade behavior is intentionally asymmetric

- **upcoming line:** with `NEXT_SUNG_LINE_EMOJIMAXX_ON_AT_FIRST = 1` (the default), EmojiMaxx is present from the first visible instant;
- **currently sung line:** EmojiMaxx stays on for the entire sung-line lifetime and never flips back to words because its brightness is changing;
- **already-sung line:** this is the only line allowed to de-EmojiMaxx back into words, after it has faded below `HIDE_PREVIOUS_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT`.
- **circled-number spacing:** number substitutions such as `❶` receive a deliberate extra safety cell whenever more lyric text follows. The normalization is applied after phrase substitution and before centering width is measured, so `This one is` becomes visually `This ❶  is` while a number at the end of a line receives no trailing padding. Leading/trailing subtitle whitespace is stripped before layout.

If `NEXT_SUNG_LINE_EMOJIMAXX_ON_AT_FIRST` is changed to `0`, the incoming line instead waits for `HIDE_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT` before the emoji appear.

### 64 random-ish examples from the current dictionary

| Example | Example | Example | Example |
|---|---|---|---|
| `world` → 🌍 | `snake` → 🐍 | `snakes` → 🐍🐍🐍 | `pirate` → 🏴‍☠️ |
| `love` → ❤️ | `heart` → 💗 | `fire` → 🔥 | `star` → ⭐ |
| `moon` → 🌙 | `home` → 🏠 | `music` → 🎶 | `song` → 🎵 |
| `dance` → 💃 | `party` → 🎉 | `cry` → 😭 | `tears` → 😢 |
| `smile` → 😊 | `laugh` → 😂 | `kiss` → 💋 | `girl` → 👧 |
| `woman` → 👩 | `eyes` → 👀 | `rain` → 🌧️ | `snow` → ❄️ |
| `money` → 💰 | `time` → ⏳ | `phone` → 📱 | `car` → 🚗 |
| `train` → 🚆 | `plane` → ✈️ | `devil` → 😈 | `angel` → 😇 |
| `dead` → ☠️ | `death` → ⚰️ | `broken` → 💔 | `king` → 🤴 |
| `queen` → 👸 | `brain` → 🧠 | `coffee` → ☕ | `computer` → 💻 |
| `diamond` → 🔷 | `dream` → 💭 | `flower` → 🌸 | `ghost` → 👻 |
| `guitar` → 🎸 | `hospital` → 🏥 | `key` → 🔑 | `lightning` → ⚡ |
| `lock` → 🔒 | `mail` → 📨 | `microphone` → 🎤 | `mountain` → ⛰️ |
| `pizza` → 🍕 | `red` → 🔴 | `robot` → 🤖 | `rocket` → 🚀 |
| `rose` → 🌹 | `skull` → 💀 | `sun` → ☀️ | `telephone` → ☎️ |
| `water` → 💧 | `wolf` → 🐺 | `address` → 📍 | `adult` → 🧑 |

The full table is far larger than these examples; these are meant to communicate the *kind* of semantic substitutions rather than turn the manual into a dump of hundreds of dictionary entries.

## 7. Karaoke style and treatment systems

Karaoke has **three independent visual dimensions**:

1. **typography style** — what Unicode glyph family represents the lyric;
2. **color treatment** — how truecolor is assigned across letters/words/lines;
3. **EmojiMaxx** — semantic word/phrase substitution, toggled separately.

That separation is why favorites/defaults can target glyph style, treatment, processing style, palette, granularity, persistence or EmojiMaxx independently instead of forcing one giant preset.

### 21 typography styles

| # | Style | What it does | Actual transformed pangram |
|---:|---|---|---|
| 1 | **Plain** | No glyph substitution; the original lyric text remains maximally readable. | `Sphinx of black quartz, judge my vow.` |
| 2 | **Fraktur** | Blackletter/Fraktur-style Unicode lettering. | `𝐒𝐩𝐡𝐢𝐧𝐱 𝐨𝐟 𝐛𝐥𝐚𝐜𝐤 𝐪𝐮𝐚𝐫𝐭𝐳, 𝐣𝐮𝐝𝐠𝐞 𝐦𝐲 𝐯𝐨𝐰.` |
| 3 | **Fraktur Clean** | Fraktur family with extra spacing for a lighter, cleaner presentation. | `𝐒 𝐩 𝐡 𝐢 𝐧 𝐱   𝐨 𝐟   𝐛 𝐥 𝐚 𝐜 𝐤   𝐪 𝐮 𝐚 𝐫 𝐭 𝐳 ,   𝐣 𝐮 𝐝 𝐠 𝐞   𝐦 𝐲   𝐯 𝐨 𝐰 .` |
| 4 | **Fraktur Framed** | Fraktur family wrapped in decorative framing marks. | `✦ 𝐒𝐩𝐡𝐢𝐧𝐱 𝐨𝐟 𝐛𝐥𝐚𝐜𝐤 𝐪𝐮𝐚𝐫𝐭𝐳, 𝐣𝐮𝐝𝐠𝐞 𝐦𝐲 𝐯𝐨𝐰. ✦` |
| 5 | **Circled** | Enclosed/circled-letter look. | `𝔖𝔭𝔥𝔦𝔫𝔵 𝔬𝔣 𝔟𝔩𝔞𝔠𝔨 𝔮𝔲𝔞𝔯𝔱𝔷, 𝔧𝔲𝔡𝔤𝔢 𝔪𝔶 𝔳𝔬𝔴.` |
| 6 | **Circled Clean** | Circled family with extra spacing. | `𝔖 𝔭 𝔥 𝔦 𝔫 𝔵   𝔬 𝔣   𝔟 𝔩 𝔞 𝔠 𝔨   𝔮 𝔲 𝔞 𝔯 𝔱 𝔷 ,   𝔧 𝔲 𝔡 𝔤 𝔢   𝔪 𝔶   𝔳 𝔬 𝔴 .` |
| 7 | **Cursive** | Script/cursive mathematical Unicode look. | `Ⓢⓟⓗⓘⓝⓧ ⓞⓕ ⓑⓛⓐⓒⓚ ⓠⓤⓐⓡⓣⓩ, ⓙⓤⓓⓖⓔ ⓜⓨ ⓥⓞⓦ.` |
| 8 | **Cursive Clean** | Cursive family with extra spacing. | `Ⓢ ⓟ ⓗ ⓘ ⓝ ⓧ   ⓞ ⓕ   ⓑ ⓛ ⓐ ⓒ ⓚ   ⓠ ⓤ ⓐ ⓡ ⓣ ⓩ ,   ⓙ ⓤ ⓓ ⓖ ⓔ   ⓜ ⓨ   ⓥ ⓞ ⓦ .` |
| 9 | **Cursive Framed** | Cursive family with decorative framing marks. | `⸎ Ⓢⓟⓗⓘⓝⓧ ⓞⓕ ⓑⓛⓐⓒⓚ ⓠⓤⓐⓡⓣⓩ, ⓙⓤⓓⓖⓔ ⓜⓨ ⓥⓞⓦ. ⸎` |
| 10 | **Uppercase** | An emphatic uppercase-oriented legacy transform. | `𝓢𝓹𝓱𝓲𝓷𝔁 𝓸𝓯 𝓫𝓵𝓪𝓬𝓴 𝓺𝓾𝓪𝓻𝓽𝔃, 𝓳𝓾𝓭𝓰𝓮 𝓶𝔂 𝓿𝓸𝔀.` |
| 11 | **Greek** | Greek-ish vowel/letter substitutions for an angular alternate alphabet. | `Sphιnx θf blλck qцλrtz, jцdgξ my vθw.` |
| 12 | **Greek Clean** | Greek-ish transform with extra spacing. | `S p h ι n x   θ f   b l λ c k   q ц λ r t z ,   j ц d g ξ   m y   v θ w .` |
| 13 | **Greek Framed** | Greek-ish transform with framing marks. | `⸎ Sphιnx θf blλck qцλrtz, jцdgξ my vθw. ⸎` |
| 14 | **Leetspeak** | Classic digit/symbol substitutions such as 4/3/1/0/5/7. | `5ph1nx 0f bl4ck qu4r7z, judg3 my v0w.` |
| 15 | **Leetspeak Clean** | Leetspeak with extra spacing. | `5 p h 1 n x   0 f   b l 4 c k   q u 4 r 7 z ,   j u d g 3   m y   v 0 w .` |
| 16 | **Symbol Mix** | A symbol-heavy closest-shape alphabet. | `§🅿hℐn❌ ⭕f 🅱l🅰ck q𝒰🅰r✝z, j𝒰dgℰ my v⭕w.` |
| 17 | **Unicode Sans** | Mathematical Unicode sans-serif alphabet. | `𝗦𝗽𝗵𝗶𝗻𝘅 𝗼𝗳 𝗯𝗹𝗮𝗰𝗸 𝗾𝘂𝗮𝗿𝘁𝘇, 𝗷𝘂𝗱𝗴𝗲 𝗺𝘆 𝘃𝗼𝘄.` |
| 18 | **Enclosed Letters** | Unicode enclosed/circled alphabet. | `Ⓢⓟⓗⓘⓝⓧ ⓞⓕ ⓑⓛⓐⓒⓚ ⓠⓤⓐⓡⓣⓩ, ⓙⓤⓓⓖⓔ ⓜⓨ ⓥⓞⓦ.` |
| 19 | **Closest Unicode** | Closest-looking Unicode/symbol replacements for selected Latin letters. | `§🅿hℐn❌ ⭕f 🅱l🅰ck q𝒰🅰r✝z, j𝒰dgℰ my v⭕w.` |
| 20 | **Script** | Retained legacy script treatment. | `Ⓢⓟⓗⓘⓝⓧ ⓞⓕ ⓑⓛⓐⓒⓚ ⓠⓤⓐⓡⓣⓩ, ⓙⓤⓓⓖⓔ ⓜⓨ ⓥⓞⓦ.` |
| 21 | **Megamix** | A deterministic **mix of all the other styles**, chosen independently per nonblank word so one lyric line can contain several typography families at once. | `§🅿hℐn❌ ⓞⓕ b l λ c k 𝗾𝘂𝗮𝗿𝘁𝘇, ⓙⓤⓓⓖⓔ 𝔪𝔶 𝐯 𝐨 𝐰 .` |


### Seven color treatments

| # | Treatment | What it does |
|---:|---|---|
| 1 | **Readable Solid** | No extra foreground-color pattern; lets glyph styling and line brightness do the work. |
| 2 | **Line Rainbow** | A continuous ROYGBIV sweep **character by character across the whole line**. |
| 3 | **Word Rainbow** | Each word advances to the next point in a rainbow sweep while letters inside the word share a color. |
| 4 | **Random Letter Color** | Each character gets a pseudo-random truecolor derived from the line seed and character position. |
| 5 | **Hashed Word Color** | Each word gets a stable SHA-256/HSL-derived color, so the same word tends to keep a recognizable color identity. |
| 6 | **Megamix1** | A **mix of the first five treatments at word granularity**: each word deterministically chooses one of them. |
| 7 | **Megamix2** | A **mix of the first five treatments at line granularity**: one treatment is deterministically selected for the whole line. |


The reference plate below is generated from the **actual treatment function**, not a hand-painted approximation:


The sentence is **“Sphinx of black quartz, judge my vow.”** so differences are visible under identical text. **Line Rainbow** colors each character along one continuous line-wide sweep; **Word Rainbow** advances the sweep once per word and keeps each word internally one color. `Megamix1` deterministically chooses among treatments 1–5 **per word**, while `Megamix2` deterministically selects one treatment 1–5 for **the entire line**.

## 8. SIXEL spectrum, album art and Chafa

SIXEL is the image-oriented graphics path and is therefore documented **before** DRCS. Album-art galleries and the SIXEL spectrum raster are prepared as image data and encoded for the terminal by **[Chafa 1.18.2](https://github.com/hpjansson/chafa/releases/tag/1.18.2)**, the known/documented version for this build.

The SIXEL path can:

1. decode embedded and sidecar artwork;
2. resize while preserving aspect ratio;
3. arrange up to 16 images into a 4×4 terminal-width-aware gallery;
4. render an FFmpeg-derived spectrum raster;
5. hand the finished raster to Chafa for SIXEL encoding;
6. reserve/clip the bottom carefully so SIXEL pixels do not bleed through a following text divider.


Chafa itself is a fast terminal graphics renderer. The script invokes it with SIXEL output and full color rather than implementing a SIXEL encoder in Python.

## 9. 🚩 Experimental DRCS soft-font visualizer

The DRCS path is the program’s most ambitious terminal renderer. **🚩 It is still experimental — it doesn’t work for the developer’s preferred terminal setup, but might work for you.** The data model is nevertheless used for the block visualizer behavior and documentation.

### V29 separates six independent visual dimensions

1. **Glyph family (25)** — what printable/block shape represents a level.
2. **Treatment (15)** — how the analyzed spectrum is interpreted before drawing.
3. **Processing style (65)** — where color phase comes from: spatial textile geometry or live signal features.
4. **Palette (32)** — the actual color set mapped onto that processing phase.
5. **Fade/color-aging mode (4)** — how retained energy changes brightness/color as it ages.
6. **Block persistence (12)** — how bar geometry itself survives over time.
7. **Granularity (3)** — one bin per cell, two Unicode half-cell bins, or two independently filled DRCS sub-bars.

Yes, that is technically seven bullets; persistence and fade are deliberately separate because one changes geometry while the other changes color/brightness.

The discrete product is **25 × 15 × 65 × 32 × 4 × 12 × 3 = 112,320,000 combinations**. Independent palette reversal doubles the visible direction states to **224,640,000**. The frequency warp, terminal size, truncated rows, audio, time, AGC gain, fade duration and blank-karaoke expansion are continuous/toggle dimensions and are not included in that number.

### Signal path

V29’s normal high-rate signal path is:

1. FFmpeg analyzes spectrum frames in low-priority rolling chunks at **30 Hz**.
2. Playback time selects and linearly interpolates between adjacent analysis frames.
3. The selected visualizer treatment turns spectral data into logical bar heights.
4. Display-only AGC normalizes legibility without modifying audio.
5. The selected persistence algorithm updates temporal block geometry.
6. Optional **Ctrl+Alt+F9 frequency warp** remaps horizontal frequency distribution while leaving the low 55% untouched.
7. The selected **processing style** produces a 0–1 phase from x/y geometry or live signal metrics.
8. The selected **palette** maps that phase into RGB.
9. Fade/color-aging modifies retained-energy brightness/color.
10. Granularity converts logical bins to cells/half-cells/twin DRCS bars.
11. ANSI/DRCS output is row-anchored with autowrap temporarily disabled.
12. If the completed frame is byte-identical to the previous one, it is not sent to the terminal.
13. Paint time feeds an adaptive scheduler that targets up to **120 Hz** but backs off if the terminal blocks.

This division matters for performance as much as design. Spatial/quilt processing grids are cached by style and geometry; palettes are cached as 256-entry RGB LUTs; the default Signal Aurora family calculates color once per frequency bin rather than once per bin *per row*; and commonly repeated RGB/DRCS blends are cached.

### Why 30-Hz analysis can still produce smoother 120-Hz motion

The FFT does not need to be recomputed at every screen refresh. If analyzed frame A represents 1.000 s and frame B represents 1.033 s, the renderer can synthesize intermediate visual frames at roughly 1.008, 1.017 and 1.025 s by interpolating the bin values. Persistence, AGC and color processing then run on those intermediate states. The audio analysis cost remains close to 30 Hz while motion can be much smoother.

The renderer’s reported `Hz:` control-row value is the **current adaptive requested paint rate**, not a promise that every Windows Terminal build physically displayed every frame.

## 10. Album-art discovery and gallery rules

Artwork can come from embedded cover data and sidecar image files. The program goes well beyond “show the first JPG in the folder.”

### Priority

Broadly:

1. cover/front
2. back
3. disc/CD art
4. `inlay*`
5. other artwork
6. matrix scans last

### Gallery geometry

- up to 4 images per row;
- up to 4 rows;
- up to 16 images total;
- images preserve aspect ratio with black letterboxing rather than being brutally cropped;
- priority groups are row-reversed so the best four are nearest the default bottom viewport.

### Duplicate suppression

The system first rejects byte-identical duplicates, then uses visual fingerprints so the same cover stored as an embedded PNG and a resized/recompressed JPEG can still collapse into one display item.

### Loose-folder sidecar protection

If a folder behaves like a loose collection where multiple audio files each have their own same-stem JPG, the player does **not** treat every JPG in that folder as album art for the current song. In that scenario it restricts display to the current track's sidecar art, preventing `Frank Sinatra - ...jpg` from being displayed alongside `Joe Dowell - ...jpg` merely because the songs share a directory.

### Divider safety

V26 retains a tiny pixel guard inside the bottom of the gallery raster. This is specifically to prevent a few SIXEL pixels from crossing a following text divider in Windows Terminal while avoiding the much uglier solution of reserving an entire blank terminal row.

## 11. Fine-grained progress bar

A normal text progress bar has one update position per character. This one uses the Unicode left-block sequence (`▏▎▍▌▋▊▉`) so the current boundary has **⅛-character resolution**.

The unplayed portion uses a tinted cell background rather than a separate black/texture character. That matters because the unused fraction of a Unicode partial-block cell inherits its background; matching that background to the rest of the unplayed bar prevents a visible black seam every time the partial block moves into the next cell.

The elapsed/total clock and percentage reserve only the space they need while the bar consumes the remaining row. Volume is deliberately moved to the controls row as compact `🔇/🔈/🔉/🔊 N%` state so it never breaks the visual continuity between the clock and bar.

## 12. Non-destructive edge-silence trimming

By default V26 treats sustained audio below **−43 dBFS** at the *beginning or end* of a track as removable playback padding. It does **not** rewrite the source file and it never skips silence in the middle of a song. The detector requires at least **0.35 seconds** of sufficiently quiet edge audio and preserves an **80 ms safety pad** around the detected audible material.

The effective audible start/end is computed once and then used by playback, looping, seeking and the progress display. Lyrics, SRT timestamps, history identities and resume bookmarks remain tied to the original source timeline so timing does not drift. If detection is uncertain, the conservative behavior is to leave the edge alone.

The defaults can be disabled or tuned with `--no-trim-edge-silence`, `--trim-silence-threshold-db`, `--trim-silence-min-duration`, and `--trim-silence-keep`.

## 13. Playlist formats and fast startup

Supported playlist formats:

- M3U
- M3U8
- PLS
- XSPF

Only usable local audio entries are included.

For line-oriented playlists, startup can seek into the file rather than requiring a full read just to choose the first song. Resume membership checks also use fast techniques so “is the saved track present?” does not secretly become the expensive full historical preparation step.

## 14. History-aware shuffle and the persistent queue

Historical shuffle is not a naïve `random.shuffle(entries)`, and after it is built it is **not repeatedly reshuffled between tracks**. The database records which tracks were heard and when. A rebuild uses that information so never-heard and long-unheard tracks are favored, with randomness inside recency groups so the order does not become a rigid oldest-first report.

The result is then a queue. Shuffle mode advances sequentially through it. Whenever playback departs a playlist track, `playlist_history_mark_played()` upserts that track into the local `played_tracks_recent` table and refreshes the in-memory last-played cache. Unless the departure is an explicit Stop/resume, the same track is then rotated to the queue tail immediately in memory. V27 snapshots that queue to a serialized background cache writer; after a short 0.75-second grace period, the newest pending snapshot is written atomically. That keeps the persistent queue durable without placing JSON serialization or disk I/O in the track-to-track hot path.

Example: `A → B → C → D` becomes `B → C → D → A` after departing A. A later process invocation therefore starts at B rather than making a fresh random choice that can land on A again.

`Ctrl+Alt+R` deliberately discards the prepared queue/cache and asks for a fresh history-biased rebuild while the current song keeps playing.

The queue-rotation diagram is shown once in the visual-reference section near the top of this manual.

## 15. Shuffle cache

A completed internal shuffle is serialized as JSON under:

```text
%TEMP%\play_audio_file\shuffle_cache\<playlist-hash>.json
```

The cache contains:

- creation time;
- playlist path identity;
- playlist file mtime and size;
- resolved usable entries;
- prepared shuffle order;
- cached last-played timestamps used by the `Last heard:` display.

A fresh cache means a later invocation can skip both the historical database pass and the 0–100% shuffle preparation. The order in that JSON is the **persistent live queue**: departing a song rotates it to the tail immediately in memory, then schedules an asynchronous cache rewrite. Rapid skips coalesce to the newest pending queue snapshot, and one daemon writer serializes updates so older writes cannot race newer queue states. Rotation preserves the original `created_at`, so normal listening cannot keep an old historical build alive forever. If the playlist changes, the cache is invalid immediately. Missing media files are filtered rather than resurrected. `Ctrl+Alt+R` deletes the cache and rebuilds on demand.

## 16. Playlist resume and back-navigation history

Playlist resume data is persisted so an interrupted song/position can be recovered. When the playlist starts again:

- if that song is still present, it resumes;
- otherwise the player chooses a new start quickly.

Previous-track navigation uses a **browser-style visit-history cursor**. This is important: simply appending every revisited song to a list causes an `E → D → E → D` two-song loop when trying to go back repeatedly. The cursor design lets `<` genuinely walk back through the playback path.

## 17. `Last heard:`

When cached/history information is available, V31 formats the prior listen as a compact **local calendar date** rather than a relative age. This is easier to recognize and usually shorter, which gives the metadata packer a better chance to keep it on an existing row:

```text
Last heard: Tuesday      # within the previous seven days
Last heard: Aug 21       # older, but in the current year
Last heard: Oct 21 ’21   # a previous year
```

The same previous-play timestamp appears in the `?` help masthead. The player does not perform a fresh per-track history query simply to paint this field during every playback transition; it reuses the local history database/runtime cache already maintained for playlist rotation and shuffle bias.

## 18. Last.fm scrobbling

Automatic scrobbling is based on **actual listened ranges**, not merely “the process has been open for N seconds.”

For a known-duration track, eligibility occurs after at least half the duration has genuinely been heard. Overlapping listened ranges are merged, so seeking backward and replaying the same minute cannot inflate eligibility.

Credentials can come from environment variables or a local `.fm` sidecar. Scrobbling is delegated to Claire's [`claire_lastfm.py`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairecjs_utils/claire_lastfm.py) helper and submission runs in a daemon thread so network work does not block visual playback.

`claire_lastfm.py` is also a standalone command-line scrobbler, not merely an internal library. For example:

```bat
python claire_lastfm.py --artist "Artist" --title "Song" --album "Album"
```

That makes it useful for manually scrobbling music from other workflows or players as well as for `play_audio_file.py`. `Ctrl+Alt+L` forces an immediate scrobble attempt for the current track from inside this player.

## 19. Last.fm log import and play-history reporting

The log importer searches the real Windows Last.fm locations, including:

```text
%LOCALAPPDATA%\Last.fm\Last.fm Scrobbler.log
%LOCALAPPDATA%\Last.fm\logs\
%LOCALAPPDATA%\Last.fm\logs\last.fm\
```

plus compatibility locations used by older versions of this project.

The pretty report canonicalizes artist identity for grouping without destructively rewriting the underlying history. Examples of equivalence include:

- `D·O·A·` and `D.O.A.`
- `Earth Wind & Fire`, `Earth, Wind & Fire`, and `Earth Wind And Fire`
- `Hank Williams Jr` and `Hank Williams Jr.`
- `Eat Babies? feat DJ Migraine` and `EAT BABIES`

`feat`, `ft`, and `featuring` suffixes are removed for report identity. Punctuation/case are ignored for matching. The displayed spelling is selected from the most frequently occurring cleaned variant, and one-off known corrections such as `Girls Ritual → Girls Rituals` are applied.

## 20. Winamp-compatible now-playing TXT/JPG files

The player periodically writes a small text record plus current artwork so the rest of the Clairevironment — or anything else that understands the same fields — can cheaply answer “what is playing?” without interrogating FFplay.

### Automatic location rule

The default is intentionally **conditional** rather than machine-specific:

1. **If `C:\mp3\lists` exists:**
   - `C:\mp3\lists\winamp_now_playing.txt`
   - `C:\mp3\lists\winamp_now_playing.jpg`
2. **Otherwise:** stay portable and write next to the script:
   - `play_audio_file-now-playing.dat`
   - `play_audio_file-now-playing.jpg`

This is what the source actually does: V26 preserves the corrected **conditional** behavior instead of unconditionally forcing the `C:\mp3\lists` target on every Windows machine.

### Compatibility with Winamp’s now-playing plugin

The text field layout deliberately provides **compatibility with Winamp’s now-playing plugin, [Aldaviva/WinampNowPlayingToFile](https://github.com/Aldaviva/WinampNowPlayingToFile)**. It uses the same field-oriented idea — full filename plus elapsed time, album, year, genre, artist, title, comment and related metadata — so custom tools can ingest the current-song record in the same general format whether Winamp or `play_audio_file.py` produced it.

That compatibility lets Winamp and `play_audio_file.py` feed the same downstream scripts/status tools instead of forcing every consumer to know which player produced the current-song record.

`--now-playing PATH` adds another target. `--no-now-playing-sidecar` suppresses the automatically chosen target while still allowing explicit `--now-playing`; `--no-now-playing` suppresses all of these files.

## 21. URL handling

The normal URL tag is the primary destination. Distinct URLs found in Comment are additional destinations only when they do not merely duplicate the real URL field. Displayed URL fields use **OSC 8 hyperlinks** where supported.

Keyboard navigation intentionally moved in V25 so `Ctrl+G` could become persistence:

- **`Ctrl+U` — URL:** open the primary URL immediately.
- **`Ctrl+B` — Browse:** if there is one URL, open it; if there are several, choose `1`, `2`, `3`, or `A` for all. **Esc aborts.** Multiple URLs open one second apart.

In Windows Terminal, OSC-8 links are also usually Ctrl+clickable depending on terminal configuration.

## 22. Winamp coexistence

This is separate from — but intentionally complementary to — compatibility with [WinampNowPlayingToFile](https://github.com/Aldaviva/WinampNowPlayingToFile), which lets Winamp write the same kind of field-oriented current-song file consumed elsewhere in Claire's scripts.

If a Winamp instance is playing, the script can pause it before taking over audio preview. The important detail is ownership: the player tracks whether **it** paused Winamp and resumes only in that case. It does not blindly send Play commands to an already-stopped Winamp instance.

The code discovers Winamp through PATH, conventional install directories, and the Windows App Paths registry location.

## 23. Persistent settings and favorites

Core UI/player settings live under:

```text
HKCU\Software\ClaireCJS\play_audio_file
```

Persisted state includes visualizer glyph/treatment mode, **processing style**, **palette**, palette-reverse state, **visualizer granularity**, persistence mode, frequency-warp state, karaoke style/treatment, EmojiMaxx state, progress style, output channels, balance, volume, speed index, loop/shuffle/autoplay, and DRCS/SIXEL enablement.

Favorites use the same registry namespace and may contain *multiple* saved values per category. V29 adds a separate `UserDefault_…` registry layer for the `*` / F1 system: each default category has exactly **one** selected value. `*` sets it, F1 applies it, and Alt+F1 swaps back to the pre-reset state. Granularity, processing style and palette all participate in both systems.

Temporary playlist shuffle order is **not** stored in the registry; it belongs in `%TEMP%` because it has an expiration policy and is disposable.

## 24. Terminal geometry and Unicode correctness

This program cares about **terminal cells**, not Python string length.

That is why it uses `wcwidth` when available and maintains a fallback for wide East Asian characters, combining marks, emoji presentation selectors, regional indicators, and ZWJ sequences.

ANSI escape sequences and OSC-8 links are explicitly ignored when measuring visible width. This is critical for:

- preventing accidental wraps;
- fitting metadata fields;
- keeping status markers on-screen;
- drawing centered karaoke correctly;
- truncating colored/clickable text safely;
- deciding whether a title should animate.

V27 deliberately avoids live VT **window-geometry query sequences** during playback. Earlier builds called `claire_terminal_geometry.query_terminal_geometry()`, which issues CSI `14t`/`16t`/`18t` window/cell queries and temporarily changes console input mode. That is technically valid, but some Windows Terminal/ConPTY setups can react to host-window operations in ways that disturb another application's fullscreen/focus state. V27 instead uses passive `GetCurrentConsoleFontEx` sizing (with a conservative fallback) for SIXEL/font-ratio calculations and ordinary `shutil.get_terminal_size()` for rows/columns.

The older track-change viewport snap based on `SetConsoleWindowInfo` is also **disabled by default** for the same focus-safety reason. If someone explicitly prefers forced scroll-to-bottom and accepts that host-window interaction, the source-only `ALLOW_WIN32_VIEWPORT_SNAP_ON_TRACK_CHANGE = 1` restores it.

---

# Visualizer catalog

The visualizer has seven major discrete axes. Because they are independently selectable, the total is **112,320,000 base combinations**:

**25 glyph families × 15 treatments × 65 processing styles × 32 palettes × 4 fade behaviors × 12 persistence modes × 3 granularity modes = 112,320,000**.

The independent palette-reverse state doubles those visible color-direction variants to **224,640,000** without consuming another style number. That count does not include fade duration, terminal width, number of rows, truncated top bands, blank-karaoke expansion, or the continuously changing source audio.

## SIXEL image visualizer first

The SIXEL path is the practical image path and uses [Chafa 1.18.2](https://github.com/hpjansson/chafa/releases/tag/1.18.2). See the generated SIXEL reference plate above and the dedicated deep-dive section.

## 🚩 DRCS experimental catalog

> 🚩 **Doesn’t work for the developer, but might work for you.** The tables below describe what the implementation is designed to emit.

### 25 glyph families

| # | Glyph family | Palette / progression | Character |
|---:|---|---|---|
| 1 | **Classic** | `abcdefghi` | Downloaded DRCS fill tiles; the intended soft-font baseline. |
| 2 | **Legacy Classic** | `abcdefghi` | Earlier/softer DRCS baseline retained for comparison. |
| 3 | **Eighth Blocks** | ` ▁▂▃▄▅▆▇█` | Unicode block-height steps from ▁ through █. |
| 4 | **Soft Blocks** | `  ░░▒▒▓▓█` | Space/░/▒/▓/█ progression with visibly soft density changes. |
| 5 | **Dense Blocks** | ` ·∙•●◉◉██` | Dots/circles into heavy blocks for a denser organic column. |
| 6 | **Half Blocks** | ` .:-=+*#@` | ASCII punctuation-to-block ramp with many intermediate densities. |
| 7 | **Thin Blocks** | ` 12345678` | Narrow numeric-looking height ladder. |
| 8 | **Wide Blocks** | ` abcdefgh` | Wide letter-like ladder before full block. |
| 9 | **Shaded Columns** | ` ○◔◑◕●◉██` | Circle/partial-circle progression into solid blocks. |
| 10 | **Stepped Columns** | ` ◌○◍◎●◉██` | Outlined-to-filled circular/column ladder. |
| 11 | **Braille** | ` ᛫᛬᛭ᛮᛯᛰ██` | Braille/rune-like fine detail before full blocks. |
| 12 | **Dots** | ` ⠁⠃⠇⡇⣇⣧⣷█` | Braille dot-cell ladder for fine low-level activity. |
| 13 | **Circles** | ` ･·•●◆◈██` | Dot → circle → diamond progression. |
| 14 | **Diamonds** | ` ˙·∙•●⬤██` | Round dot progression into heavy circular/diamond shapes. |
| 15 | **Runes** | ` ⌞⌜╞╠╬▓██` | Angular box/rune marks growing toward solid fill. |
| 16 | **Stars** | ` _▁▂▃▄▆▇█` | Underscore/block height ramp; intentionally clean skyline look. |
| 17 | **Math Symbols** | ` .oO0@#██` | ASCII/math-style `.oO0@#` growth. |
| 18 | **Gothic Marks** | ` ,;irsXA#` | Fine punctuation/letter density ramp. |
| 19 | **Sparkles** | ` `'^~*=#@` | Quote/caret/star/hash density ramp. |
| 20 | **ASCII Fine** | ` ㆍ◦○◉●◆██` | Small East-Asian/circle-like marks to diamond/block. |
| 21 | **ASCII Heavy** | ` ︱▏▎▍▌▋▊█` | Vertical fractional blocks for a sharp meter look. |
| 22 | **Digital** | ` ︳┃┃╋╋▓██` | Tall digital/box-drawing marks into solid blocks. |
| 23 | **Needles** | ` ⋅∘∙●◉⬢██` | Centered dots/circles into polygon/block peaks. |
| 24 | **Rounded** | ` ｡ﾟ･:*:▓█` | Tiny punctuation/star shapes with rounded energetic peaks. |
| 25 | **Minimal** | ` .·°º¤ø██` | Very restrained dot/degree/currency-like progression into blocks. |


### 15 spectrum-shaping treatments

| # | Treatment | Actual shaping intent |
|---:|---|---|
| 1 | **Punch** | No smoothing radius; direct, comparatively immediate response with moderate gain. |
| 2 | **Balanced** | Light radius-1 smoothing plus valley tightening; more separation between active peaks and the floor. |
| 3 | **Soft** | Radius-2 smoothing with a low gamma that lifts quieter material into a broad, soft shape. |
| 4 | **Tight** | Heavy radius-3 smoothing followed by nonlinear compression; dense/compact movement rather than spiky detail. |
| 5 | **Smooth** | No neighborhood blur, but amplitudes are quantized to eighth steps and lifted by a low gamma for a smooth-stepped skyline. |
| 6 | **Pulse** | Radius-1 smoothing plus extra high-frequency emphasis and stronger gamma compression; intentionally restrained except on transient detail. |
| 7 | **Skyline** | Radius-2 smoothing plus valley tightening; emphasizes separated building-like peaks. |
| 8 | **Peaks** | No neighborhood smoothing, with a moderately high gamma and lower gain for sharper isolated peaks. |
| 9 | **Compressed** | Radius-3 smoothing plus nonlinear compression; fills more of the available vertical range with dense motion. |
| 10 | **Expanded** | Radius-1 smoothing, stepped eighth-level quantization and stronger gamma; spreads the apparent dynamic range into discrete tiers. |
| 11 | **Transient** | No smoothing plus frequency-dependent emphasis toward the right/high-frequency side; reacts strongly to sparks/transients. |
| 12 | **Valleys** | Radius-2 smoothing plus valley tightening with high gamma/low gain; deliberately carves out low areas. |
| 13 | **Wide** | Very wide radius-4 smoothing and very low gamma; broad, large-scale spectrum movement. |
| 14 | **Hot** | No smoothing plus nonlinear compression, yielding a bright/high-energy presentation without the widest blur. |
| 15 | **Quiet** | Radius-1 smoothing plus eighth-step quantization with restrained gain; calmer, discretized motion. |


### 65 processing styles

Processing styles produce phase/structure; they do **not** own a fixed color set. Styles 47–65 are signal-driven (`⚡`), including four Signal Aurora variants.

| # | Processing style | Intent |
|---:|---|---|
| 1 | **Vertical Flow** | Vertical position supplies phase; useful for smooth bottom→top palette gradients. |
| 2 | **Candy Stripe** | Repeating stripe phase creates candy-like alternating bands. |
| 3 | **Three Bands** | Divides horizontal frequency space into three broad phase regions. |
| 4 | **Frequency Zones** | Maps frequency zones to repeating palette regions. |
| 5 | **Checker Spectrum** | Alternating x/y checks; especially effective with high-contrast palettes. |
| 6 | **Plaid** | Crossing horizontal/vertical textile bands; one of the strongest quilt-friendly processors. |
| 7 | **Nine-Patch Quilt** | Repeating nine-patch block geometry. |
| 8 | **Radial Sweep** | Phase radiates from a center point. |
| 9 | **Diagonal Sweep** | Phase runs diagonally across the spectrum. |
| 10 | **Radial Spectrum** | Radial phase tied to spectrum coordinates. |
| 11 | **Argyle** | Diamond lattice geometry. |
| 12 | **Tartan** | Layered woven horizontal/vertical bands. |
| 13 | **Log Cabin Quilt** | Repeating textile/patchwork phase geometry based on **Log Cabin Quilt**; combine it with any palette. |
| 14 | **Pinwheel Quilt** | Repeating textile/patchwork phase geometry based on **Pinwheel Quilt**; combine it with any palette. |
| 15 | **Diamond Quilt** | Repeating textile/patchwork phase geometry based on **Diamond Quilt**; combine it with any palette. |
| 16 | **Basket Weave** | Repeating textile/patchwork phase geometry based on **Basket Weave**; combine it with any palette. |
| 17 | **Houndstooth** | Repeating textile/patchwork phase geometry based on **Houndstooth**; combine it with any palette. |
| 18 | **Chevron Quilt** | Repeating textile/patchwork phase geometry based on **Chevron Quilt**; combine it with any palette. |
| 19 | **Mosaic Quilt** | Repeating textile/patchwork phase geometry based on **Mosaic Quilt**; combine it with any palette. |
| 20 | **Star Quilt** | Repeating textile/patchwork phase geometry based on **Star Quilt**; combine it with any palette. |
| 21 | **Brickwork** | Repeating textile/patchwork phase geometry based on **Brickwork**; combine it with any palette. |
| 22 | **Hex Weave** | Repeating textile/patchwork phase geometry based on **Hex Weave**; combine it with any palette. |
| 23 | **Confetti** | Spatial phase pattern based on **Confetti**; colors come from the independently selected palette. |
| 24 | **Circuit Board** | Spatial phase pattern based on **Circuit Board**; colors come from the independently selected palette. |
| 25 | **Zebra Neon** | Spatial phase pattern based on **Zebra Neon**; colors come from the independently selected palette. |
| 26 | **Polka Dots** | Spatial phase pattern based on **Polka Dots**; colors come from the independently selected palette. |
| 27 | **Stained Glass** | Repeating textile/patchwork phase geometry based on **Stained Glass**; combine it with any palette. |
| 28 | **Crosshatch** | Repeating textile/patchwork phase geometry based on **Crosshatch**; combine it with any palette. |
| 29 | **Spiral Quilt** | Repeating textile/patchwork phase geometry based on **Spiral Quilt**; combine it with any palette. |
| 30 | **Wave Interference** | Spatial phase pattern based on **Wave Interference**; colors come from the independently selected palette. |
| 31 | **Flying Geese Quilt** | Repeating textile/patchwork phase geometry based on **Flying Geese Quilt**; combine it with any palette. |
| 32 | **Ohio Star Quilt** | Repeating textile/patchwork phase geometry based on **Ohio Star Quilt**; combine it with any palette. |
| 33 | **Bear Paw Quilt** | Repeating textile/patchwork phase geometry based on **Bear Paw Quilt**; combine it with any palette. |
| 34 | **Tumbling Blocks Quilt** | Repeating textile/patchwork phase geometry based on **Tumbling Blocks Quilt**; combine it with any palette. |
| 35 | **Rail Fence Quilt** | Repeating textile/patchwork phase geometry based on **Rail Fence Quilt**; combine it with any palette. |
| 36 | **Irish Chain Quilt** | Repeating textile/patchwork phase geometry based on **Irish Chain Quilt**; combine it with any palette. |
| 37 | **Drunkard Path Quilt** | Repeating textile/patchwork phase geometry based on **Drunkard Path Quilt**; combine it with any palette. |
| 38 | **Kaleidoscope Quilt** | Repeating textile/patchwork phase geometry based on **Kaleidoscope Quilt**; combine it with any palette. |
| 39 | **Lone Star Quilt** | Repeating textile/patchwork phase geometry based on **Lone Star Quilt**; combine it with any palette. |
| 40 | **Courthouse Steps Quilt** | Repeating textile/patchwork phase geometry based on **Courthouse Steps Quilt**; combine it with any palette. |
| 41 | **Storm At Sea Quilt** | Repeating textile/patchwork phase geometry based on **Storm At Sea Quilt**; combine it with any palette. |
| 42 | **Snail Trail Quilt** | Repeating textile/patchwork phase geometry based on **Snail Trail Quilt**; combine it with any palette. |
| 43 | **Card Trick Quilt** | Repeating textile/patchwork phase geometry based on **Card Trick Quilt**; combine it with any palette. |
| 44 | **Prairie Points Quilt** | Repeating textile/patchwork phase geometry based on **Prairie Points Quilt**; combine it with any palette. |
| 45 | **Cathedral Window Quilt** | Repeating textile/patchwork phase geometry based on **Cathedral Window Quilt**; combine it with any palette. |
| 46 | **Trip Around World Quilt** | Repeating textile/patchwork phase geometry based on **Trip Around World Quilt**; combine it with any palette. |
| 47 | **Amplitude** | ⚡ Instantaneous normalized bar amplitude chooses palette phase. |
| 48 | **Impact** | ⚡ Attack/impact ratio emphasizes newly arriving energy. |
| 49 | **Energy Heat** | ⚡ Retained energy itself drives phase. |
| 50 | **Transient Flash** | ⚡ Fast attacks flash toward different palette regions than steady material. |
| 51 | **Bass Pulse** | ⚡ Bass-weighted live energy controls phase. |
| 52 | **Midrange Pulse** | ⚡ Midrange-weighted live energy controls phase. |
| 53 | **Treble Spark** | ⚡ Treble-weighted attack/energy produces spark-like phase changes. |
| 54 | **Persistence Age** | ⚡ Current-versus-retained energy exposes persistence age. |
| 55 | **Crest Factor** | ⚡ Peak-to-neighborhood energy ratio (crest factor) drives phase. |
| 56 | **Spectral Density** | ⚡ Overall spectral occupancy/density drives phase. |
| 57 | **Local Contrast** | ⚡ Contrast against neighboring bins controls phase. |
| 58 | **Peak Proximity** | ⚡ Distance from the instantaneous bar peak changes phase vertically. |
| 59 | **Energy Plaid** | ⚡ Plaid geometry is modulated by live retained energy and impact. |
| 60 | **Dynamic Checker** | ⚡ Checker selection changes with frequency, row and current energy. |
| 61 | **Loudness Zones** | ⚡ Quantizes retained loudness into palette zones. |
| 62 | **Signal Aurora** | ⚡ Classic frequency + retained energy + impact Aurora processing. |
| 63 | **Signal Aurora Full Spectrum** | ⚡ Broader Aurora traversal designed to exercise nearly the full palette spectrum. |
| 64 | **Signal Aurora Prism** | ⚡ Aurora variant emphasizing local contrast, crest factor and instantaneous level. |
| 65 | **Signal Aurora Storm** | ⚡ Broad Aurora with deterministic per-frequency turbulence driven by energy/impact. |

### 32 palettes

Palettes are reusable RGB sets. `C`/`Shift+C` changes them, `Alt+Shift+C` reverses them, and the same palette can be applied to every processing style.

![All 32 V29 palettes](images/v29_palettes_32.png)

| # | Palette | Character |
|---:|---|---|
| 1 | **Full Rainbow** | Saturated ROYGBIV-style full-spectrum loop. |
| 2 | **Pastel Rainbow** | Softer high-value rainbow with reduced saturation. |
| 3 | **Fire** | Black/red → orange → hot yellow. |
| 4 | **Ocean** | Deep navy → blue/cyan → seafoam. |
| 5 | **Forest** | Near-black green → leaf green → yellow-green highlight. |
| 6 | **Toxic** | Acid green/yellow fluorescent ramp. |
| 7 | **Sunset** | Deep violet → magenta/red → warm gold. |
| 8 | **Magenta-Cyan** | Short high-contrast magenta/violet/cyan set. |
| 9 | **Purple-Gold** | Purple/violet into gold/cream. |
| 10 | **Red-White-Blue** | Red → white → blue. |
| 11 | **Cyan-Yellow** | Cyan/greenish cyan → yellow. |
| 12 | **Monochrome Green** | Green intensity ladder. |
| 13 | **Monochrome Amber** | Amber intensity ladder. |
| 14 | **Monochrome Cyan** | Cyan intensity ladder. |
| 15 | **Monochrome Violet** | Violet intensity ladder. |
| 16 | **Neon Pastel** | Bright candy-neon pastels. |
| 17 | **Heatmap** | Dark purple → red/orange → yellow heat ramp. |
| 18 | **Plasma** | Deep blue-violet → magenta → orange/yellow. |
| 19 | **Aurora** | Blue/teal/green/violet/pink northern-lights set. |
| 20 | **Ice** | Navy/blue → icy cyan → white. |
| 21 | **Candy** | Pink/gold/cyan/violet candy colors. |
| 22 | **RGB** | Red → green → blue primary sequence. |
| 23 | **CMY** | Cyan → magenta → yellow subtractive-primary sequence. |
| 24 | **Jewel** | Amethyst/sapphire/emerald/gold/ruby tones. |
| 25 | **Halloween** | Black-purple → orange/gold → deep violet. |
| 26 | **Vaporwave** | Purple/pink/cyan pastel neon. |
| 27 | **Synthwave** | Dark violet → electric violet/pink → cyan. |
| 28 | **Earth** | Brown/ochre/leaf green/sand. |
| 29 | **Rose Gold** | Wine → rose → peach → cream. |
| 30 | **Electric Blue** | Near-black blue → saturated blue → cyan-white. |
| 31 | **Lime-Magenta** | Purple/magenta contrasted with fluorescent lime/yellow. |
| 32 | **White Hot** | Black/charcoal → steel gray → white. |

The processing/palette cross-product is the core V29 change: **65 × 32 = 2,080** processing/color combinations before glyph, treatment, fade, persistence or granularity are considered.

### Four fade/color-aging behaviors

| # | Fade behavior | What it does |
|---:|---|---|
| 1 | **Energy dim** | Retained energy becomes progressively dimmer. |
| 2 | **ROYGBIV decay** | Aging energy migrates through the rainbow as it fades. |
| 3 | **Hard cutoff** | Weak retained energy is aggressively suppressed. |
| 4 | **Pulse decay** | Retention brightness is weighted into a punchier pulse-like decay. |

### Twelve block-persistence behaviors — deterministic V26 block documentation

These alter the **bar geometry over time**, so they multiply rather than replace the four fade/color-aging choices.

The deterministic block-progression plate for all twelve modes is shown once near the top of this manual. Every mode receives exactly the same `hit → quiet → quiet → quiet → new hit → quiet` input, so the visible difference comes from the algorithm rather than unrelated captured frames.



| # | Persistence | Block behavior |
|---:|---|---|
| 1 | **Peak Hold + Fall** | Peaks hold briefly, then descend at a controlled rate. |
| 2 | **Ghost Frames** | Several older block silhouettes remain as weighted ghosts behind the live shape. |
| 3 | **Comet Trails** | Current blocks form a bright head while older height falls away as a fast trail. |
| 4 | **Heat Memory** | Frequently energized bins stay elevated longer, like accumulated heat. |
| 5 | **Spring / Bounce** | Bar heights use damped velocity and can overshoot/settle. |
| 6 | **Beat Flash** | Very quick attack and short exponential retention for percussion. |
| 7 | **Echo Ladder** | Older block silhouettes return as discrete stepped echoes. |
| 8 | **Phosphor Glow** | Smooth CRT-like retention; the V26 default and closest to the older visualizer feel. |
| 9 | **Shadow Peaks** | A dim held peak remains behind the instantaneous block height. |
| 10 | **Gravity Trails** | Old blocks fall faster when taller, creating gravity-like descent. |
| 11 | **Freeze + Melt** | Strong peaks freeze for a randomized short hold and then melt unevenly. |
| 12 | **Waterfall Smear** | Recent block history is weighted together into a vertically smeared memory. |

Controls: `Ctrl+G`/`Ctrl+Shift+G` next/previous, `Alt+G` favorite cycle, `Ctrl+Alt+G` favorite toggle.

### Combination count

**25 glyph families × 15 treatments × 65 processing styles × 32 palettes × 4 fade behaviors × 12 persistence behaviors × 3 granularity modes = 112,320,000** discrete combinations. Palette reversal doubles the visible direction variants to **224,640,000**. Continuous dimensions such as audio itself, terminal width, fade duration, visible rows, and time are not counted.

### Horizontal visualizer granularity — Twin DRCS remains the V29 default

The two higher-resolution ideas are fully implemented rather than mockups. `Shift+F4` cycles:

1. **2× Twin DRCS (default)** — two logical frequency bins per terminal cell, with independent left/right 0…8-height sub-bars encoded into downloaded soft glyphs.
2. **2× Half Cells** — two bins per cell using left/right half-cell geometry (`▌` / `▐`) and independent colors where possible.
3. **1× Cells** — the original one-bin-per-cell mode; this most directly exposes the selected glyph family.

The spectrum timeline is analyzed at two-bin density once, so switching among these modes reuses existing data. The selected granularity is stored with the other player preferences. It is also **favoriteable** (`F`, then `G`) and **defaultable** (`*`, then `G`), so F1 can always return to Twin DRCS or whichever granularity you choose.

The three-mode granularity plate is shown once in the visual-reference section near the top of this manual.

# Files the program creates or uses

| Path / file | Purpose |
|---|---|
| `C:\mp3\lists\winamp_now_playing.txt` | Preferred Winamp-compatible current-song text **only when `C:\mp3\lists` already exists**. |
| `C:\mp3\lists\winamp_now_playing.jpg` | Matching current artwork **only when `C:\mp3\lists` already exists**. |
| `play_audio_file-now-playing.dat` beside the script | Portable default current-song data when `C:\mp3\lists` does **not** exist. |
| `play_audio_file-now-playing.jpg` beside the script | Portable matching artwork when `C:\mp3\lists` does **not** exist. |
| `%TEMP%\play_audio_file\shuffle_cache\*.json` | Expiring **live shuffled queue** + last-heard cache; rewritten as departed songs rotate to the tail. |
| `lastfm_play_history.csv` beside script | Generated historical play database/export. |
| `play_audio_file.fm` beside script | Optional Last.fm API credential sidecar. |
| `play_audio_file-lastfm.log` | Scrobble diagnostic log; preferred location depends on environment. |
| `HKCU\Software\ClaireCJS\play_audio_file` | Persistent player settings, favorites, playlist resume data. |

---

# Dependencies and environment

The player is intentionally layered: basic audio playback needs very little, while the most extravagant terminal graphics obviously require more.

## Required for normal audio playback

- **Python 3**
- **FFmpeg / FFplay / FFprobe** on `PATH` — FFplay is the playback engine; FFprobe supplies ordinary metadata/duration; FFmpeg supplies spectrum analysis and several image/audio conversions.

## SIXEL artwork and image-spectrum path

- **[Chafa 1.18.2](https://github.com/hpjansson/chafa/releases/tag/1.18.2)** — this is the documented/known version for the V26 build. Chafa is used to turn prepared images into SIXEL output.
- a terminal that actually renders SIXEL; Windows Terminal behavior depends on the Windows/Terminal build and graphics-path details.
- **Pillow (`PIL`)** — artwork decoding, resizing, visual fingerprints/deduplication, compositing, JPEG writing and gallery preparation.

Installation examples:

```bat
winget install -e --id hpjansson.Chafa
pip install --upgrade pillow
```

## 🚩 Experimental DRCS soft-font path

> 🚩 **Doesn’t work for the developer, but might work for you.**

By default, the analyzer still computes the full visualizer height, but the top **2** highest/rarest rows are intentionally not emitted to the terminal (`TRUNCATE_TOP_VISUALIZER_LINES = 1`). This is a display crop, not a change to spectrum analysis and not two blank rows.

DRCS uses DEC downloadable/soft character sets. Terminal support is much less consistent than ordinary ANSI/Unicode/SIXEL behavior, so this is explicitly experimental. NumPy can accelerate spectrum-frame analysis but the source also contains a pure-Python fallback.

## Unicode width: `wcwidth`

The strongly recommended [`wcwidth`](https://wcwidth.readthedocs.io/en/latest/) Python package measures the **displayed terminal-cell width** of Unicode rather than naïvely equating one Python code point with one column. That matters for emoji, combining marks, East Asian wide characters, ZWJ sequences and the player's aligned metadata/karaoke geometry. The package is also available from [PyPI](https://pypi.org/project/wcwidth/).

```bat
pip install --upgrade wcwidth
```

A dependency-free fallback exists, but `wcwidth` is preferable.

## `clairecjs_utils` / site library placement

The source explicitly adds:

```text
C:\clairecjs_utils
```

to `sys.path`, which supports Claire's traditional flat utility-module installation. **It can also live in Python's site-library / `site-packages` area** as long as the expected import names resolve. The Claire helpers relevant to this player are:

- [`claire_terminal_geometry.py`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairecjs_utils/claire_terminal_geometry.py) — live Windows Terminal geometry and character-cell pixel sizing; importable as `clairecjs_utils.claire_terminal_geometry` from a package/site-packages installation.
- [`claire_progressbar.py`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairecjs_utils/claire_progressbar.py) — Claire's reusable rainbow-aware progress-bar helper. The player accepts either `clairecjs_utils.claire_progressbar` or a flat `claire_progressbar.py` beside the player; if neither can be obtained, it falls back to a harmless no-op progress bar.
- [`claire_lastfm.py`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairecjs_utils/claire_lastfm.py) — Last.fm authentication/scrobbling helper; usable both as an imported library and directly from the command line.
- [`claire_console.py`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairecjs_utils/claire_console.py) — a broader Clairevironment ANSI/color utility sibling used elsewhere in Claire's scripts; it is linked here because it is part of the same installable utility family even though this player does not require it for its core rendering path.

In other words, `C:\clairecjs_utils` is a convenient supported location, not the only valid Python import location; a conventional package/site-packages installation is also fine when the import names above resolve correctly. V26 accepts **flat copies beside `play_audio_file.py`** and, on Windows, will make a best-effort attempt to **auto-download any missing Claire helpers beside the script with a visible download progress bar**. Set the source-only `AUTO_DOWNLOAD_CLAIRE_LIBRARIES = 0` if you explicitly do not want that self-healing behavior.

### Copy/install the Claire helpers beside `play_audio_file.py`

If you already have Claire's traditional `C:\clairecjs_utils` tree, from the directory containing `play_audio_file.py`:

```bat
copy C:\clairecjs_utils\claire_console.py .
copy C:\clairecjs_utils\claire_lastfm.py .
copy C:\clairecjs_utils\claire_progressbar.py .
copy C:\clairecjs_utils\claire_terminal_geometry.py .
```

Or download the current GitHub copies with PowerShell:

```powershell
$b='https://raw.githubusercontent.com/ClaireCJS/clairecjs_bat/main/BAT-and-UTIL-files-1/clairecjs_utils'
'claire_console.py','claire_lastfm.py','claire_progressbar.py','claire_terminal_geometry.py' | % { iwr "$b/$_" -OutFile $_ }
```

The player performs essentially that GitHub download itself when a helper is missing. Failure to download is **non-fatal** where a fallback exists; the player reports the failed helper and continues as far as the requested feature permits.

## Other useful Python packages

- **NumPy** — optional acceleration for spectrum analysis.
- **Pillow** — effectively required for the richer artwork/compositing/deduplication features.

## Windows Terminal

The UI assumes a modern terminal capable of UTF-8, ANSI truecolor, cursor positioning, OSC-8 hyperlinks and the DEC double-height sequences used for karaoke. Individual experimental graphics features have additional terminal requirements as described above.

# Troubleshooting

## “I changed the script but it behaves like an older copy”

Run:

```bat
play_audio_file.py --which-script
where.exe play_audio_file.py
```

The first command prints the exact resolved executing path; the second shows PATH candidates.

## Visualizer is sluggish for the first several seconds / suddenly turns into a wall

V26 keeps and tightens the paced background spectrum pipeline for this. Earlier chunked analysis could consume CPU/disk/network as quickly as possible during startup, and independently published chunk timing could make a later timeline handoff look radically different. V26 now:

- waits briefly so FFplay/UI/metadata work starts first;
- publishes a tiny two-second starter chunk;
- analyzes four-second chunks while staying only about **3 seconds ahead** of live playback;
- runs FFmpeg single-threaded and below-normal priority on Windows;
- resets timestamps on every chunk (`asetpts=PTS-STARTPTS`);
- forces each chunk to an exact frame count before appending it, so a background handoff cannot shift playback-to-spectrum indexing;
- **never clamps an ahead-of-analysis playhead to the analyzer’s last available frame**; if analysis is briefly behind, old blocks decay/blank until the correct time slice exists instead of freezing on FFmpeg’s sometimes-pathological final flush frame;
- uses a stable absolute spectrum scale so a near-silent chunk cannot normalize itself into a full-height wall;
- caches a completed timeline under `%TEMP%\play_audio_file\spectrum_cache` for later invocations.

Changing F6/F7 also clears temporal persistence state before repainting, so the new glyph family does not inherit a stale block-history shape.

V26 also repairs the opposite V25 symptom: a spectrum that was **present but almost completely dark**. Adaptive visual AGC boosts quiet-but-real spectrum data toward useful height, while a minimum-signal gate and hard gain ceiling keep silence/noise from becoming a fake wall. This changes only rendering, never audio.

## No visualizer

Check:

```bat
where.exe ffmpeg
where.exe ffplay
```

For SIXEL:

```bat
where.exe chafa
```

Then confirm the terminal actually supports SIXEL. The separate **🚩 DRCS soft-font path is experimental — it doesn’t work for the developer, but might work for you.**

## Album art from another track appears in a loose folder

The current code specifically detects folders where individual audio tracks have same-stem JPGs and restricts the current track to its own sidecar art. If this still happens, inspect whether the filenames actually share a stem after extension removal or whether a generic `cover.jpg` is also present.

## Duplicate artwork still appears

The deduper uses both raw hashes and tolerant visual fingerprints. Very heavily cropped/recolored/annotated variants may be genuinely different enough to survive. In that case, the relevant thresholds are inside `_album_art_fingerprints_match()`.

## Karaoke exists but does not display

Priority is `.srt` then `.lrc`, then looser fallbacks. Check:

- sidecar base name exactly matches the audio file;
- SRT timestamp syntax is conventional; V26 also tolerates comment/header lines before cue 1;
- the sidecar is readable as UTF-8 or UTF-16;
- the current cue time actually overlaps playback.

## URL is blue/visible but not clickable

OSC-8 click behavior is terminal-dependent. In Windows Terminal, try **Ctrl+click**. `Ctrl+U` (primary URL) and `Ctrl+B` (URL browser) do not depend on click support and remain the keyboard fallbacks.

## `[shuffling 90%–100%]` appears after work is done

The current logic repaints both the Playing row and controls row on background-status changes and avoids freezing live shuffle progress into permanent `Played:` lines. A completed cache should not fake a shuffle-progress cycle at all.

## Weird Unicode width/wrapping

Install/update `wcwidth`. The built-in fallback handles many cases, but terminal/font-specific emoji geometry can still be peculiar, especially with DEC double-height mode.

---

# Design philosophy

A lot of the code exists because terminal media UIs fail in small, annoying ways if they are designed as though a terminal were just a monospaced string buffer.

`play_audio_file.py` tries to do the opposite:

- measure **display cells**, not code points;
- keep ANSI styling separate from width calculations;
- preserve clickable-link state across truncation;
- distinguish “row reserved” from “row actually painted”;
- never use per-track history database work in the hot playback path when it can be prepared/cached;
- start playlist audio before expensive shuffle preparation;
- avoid inventing metadata;
- prefer lyric formats with explicit end timing;
- make experimental toggles visibly report whether they actually registered;
- treat the terminal title, scrollback, visualizer, artwork raster, and text cursor as separate pieces of state that can interfere with each other;
- keep Esc safe during normal playback while still making it the obvious way out of modal overlays.

The result is intentionally idiosyncratic. It is optimized for an extremely information-dense Windows Terminal playback experience rather than for being a generic cross-platform library. That is also why it can do things a conventional tiny CLI player would never bother attempting: double-height karaoke, RGB throb animation, history-aware persistent shuffle queue, multi-scan album art, URL launching, visual favorites, and a spectrum that literally expands upward when lyrics leave room for it, and a visualizer design space with **112,320,000** discrete glyph/treatment/color/fade/persistence combinations — **224,640,000** visible direction variants when independent color reversal is counted.

---

# Developer map: where to look in the source

The script is intentionally still a single Python file, but the major concepts are reasonably separable by function families:

- **playlist loading / random selection** — `load_playlist`, `quick_random_playlist_track`, navigation helpers
- **history identity and scoring** — `playlist_history_*`
- **shuffle queue/cache** — `playlist_shuffle_cache_path`, `load_playlist_shuffle_cache`, `save_playlist_shuffle_cache`, `rotate_playlist_queue_after_play`, `rotate_playlist_queue_to_front`, `force_rebuild_playlist_shuffle`
- **metadata** — `probe_audio_metadata`, raw broken-ID3 recovery helpers
- **lyrics** — `_read_lyrics_sidecar_text`, `load_lyrics`, `lyric_at`, `lyric_title_text_at`, neighbor fade helpers
- **Unicode/terminal width** — `terminal_cell_width`, `truncate_ansi_to_cells`, `wrap_to_cells`
- **tag panel** — `format_tag_panel`
- **keyboard decoder** — `interpret_console_key`, Windows async-key helpers
- **visualizer analysis** — `analyze_spectrum`, `spectrum_frame_at`
- **visualizer transforms** — `visualizer_mode_heights`, `visualizer_color`, DRCS renderer, V28 row-origin/autowrap stability guards
- **artwork** — `_album_art_candidates`, `extract_album_art`, `extract_album_art_variants`, `render_preplay_album_cover`
- **SIXEL visualizer** — `render_sixel_visualizer`, `composite_album_art_background`
- **Winamp-compatible now-playing files** — `write_now_playing_data`, `write_now_playing_art`
- **main interactive state machine** — `play_audio_file`
- **Last.fm** — credentials/logging/scrobble helpers and history parser/report functions
- **CLI** — `main`

---

# External references used by this manual

- [Chafa 1.18.2 release](https://github.com/hpjansson/chafa/releases/tag/1.18.2) — the documented Chafa version for SIXEL conversion in this build.
- [`wcwidth` documentation](https://wcwidth.readthedocs.io/en/latest/) and [`wcwidth` on PyPI](https://pypi.org/project/wcwidth/) — terminal-cell-aware Unicode measurement.
- [Aldaviva/WinampNowPlayingToFile](https://github.com/Aldaviva/WinampNowPlayingToFile) — the Winamp plugin whose field-oriented current-song output is intentionally compatible with this player's preferred TXT layout.
- [`claire_lastfm.py`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairecjs_utils/claire_lastfm.py) — Claire's importable and command-line Last.fm scrobbler.
- [`claire_terminal_geometry.py`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairecjs_utils/claire_terminal_geometry.py) — terminal/cell geometry helper. V27 still ships/bootstrap-supports it for Clairevironment compatibility and standalone use, but the player no longer polls its VT window-query path during live playback.
- [`claire_progressbar.py`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairecjs_utils/claire_progressbar.py) — reusable progress-bar helper.
- [`claire_console.py`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairecjs_utils/claire_console.py) — sibling Clairevironment ANSI/color utility library.
- [`generate-filelists-by-attribute.pl`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/generate-filelists-by-attribute.pl) — Claire's playlist/attribute generator whose base attribute semantics V32 mirrors for live display.
- [`generate-filelists-by-attribute-audio.ini`](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/generate-filelists-by-attribute-audio.ini) — the audio configuration used with `generate-filelists-by-attribute.pl -g -i...`.

---

# V28 additions at a glance

- **Stable spectrum row origins:** visualizer painting temporarily disables VT autowrap and explicitly homes every block row to column 1, eliminating the intermittent one-cell horizontal row drift seen with dense half-cell/DRCS output.
- **Compact state-aware current-track header:** `▶ Play:` while playing and `⏸ Play:` while paused replace the older speaker + `Playing:` label. The shorter label leaves more room for path and metadata alignment.
- **Consistent number-emoji spacing:** circled/dingbat number substitutions are normalized after all EmojiMaxx phrase/word replacements so every number gets the same extra visual separation when text follows, but no pointless padding at line end.
- V27 focus-safe terminal behavior, asynchronous shuffle-cache persistence, V26 persistent queue/history verification, visual AGC, persistence, granularity, and all previously documented controls remain intact.

# V27 additions at a glance

- **Focus-safe terminal geometry:** no live CSI window-geometry polling, and the old `SetConsoleWindowInfo` viewport snap is disabled by default so the player does not interfere with another application's fullscreen/focus state.
- **Non-blocking shuffle-cache persistence:** the queue rotates immediately in memory, while one serialized background writer saves the newest snapshot after a 0.75-second grace period.
- `alone` is removed from EmojiMaxx semantic substitutions.
- V26's persistent history-biased queue, `Ctrl+Alt+R` rebuild, verified history DB upsert, visual AGC, 3-way granularity selector, paced spectrum analysis, and deterministic persistence documentation are retained. V28 additionally locks each spectrum row to column 1 and uses a compact state-aware `Play:` header.

# Final one-line pitch

**`play_audio_file.py` is what happens when “just preview this MP3” evolves into a terminal-native music workstation that refuses to accept that command-line playback has to be visually boring, historically ignorant, metadata-fragile, or interaction-poor.** 🎧🌈🎤📊🖼️


---

## V30 troubleshooting note: horizontal bands at high repaint rates

If the visualizer height/shape looks correct but whole horizontal terminal rows appear to belong to different moments, treat that as a **presentation tear**, not a spectrum-analysis error. V30's synchronized-output + explicit-row-advance path exists specifically for this case. If a particular terminal ignores synchronized output and still tears at 120 Hz, lowering `--visualizer-target-fps` to 90 or 60 is a useful diagnostic: if the bands disappear while the spectrum shape stays identical, terminal presentation throughput is the limiting factor rather than FFmpeg analysis.
