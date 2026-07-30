# audit_music_batch.py

`audit_music_batch.py` audits incoming music batches for:

- missing or questionable title, artist, album, genre, comment, and URL tags
- missing ReplayGain track gain/peak tags
- missing, multiple, or sidecar-less embedded cover artwork, with optional
  conservative release-art discovery
- missing embedded plain lyrics or timed karaoke on vocal tracks
- unsupported audio formats and matching MP3/FLAC duplicates
- active TODOs, suspicious filenames, and zero-byte files
- disposable sidecars, transcription leftovers, logs, and kept backups
- archive/do-not-play folders missing their marker or `attrib.lst` rules

Every finding is explained. Supported actions can be applied immediately after
interactive confirmation; judgment calls remain visible without being presented
as executable actions. The checks reflect the recurring workflow rules from
`C:\notes\audio-processing-batch-NOTES.txt`.

The auditor is self-contained; lyric embedding, timed-karaoke embedding, artwork
extraction, and single-front-cover enforcement do not require a separate
`process_ready_batch.py` helper.

## Flags

`--no-interactive`

Strictly read-only: report findings without prompts or changes.

`--write-reports`

Write JSON, Markdown, and text reports.

`--output-dir FOLDER`

Write reports to a selected folder instead of the audited folder.

`--format text|json|markdown`

Select the standard-output report format.

`--max-examples NUMBER`

Limit how many audit findings are printed in each standard-output section;
`0` prints every finding.

`--include-archives`

Include archived/deprecated audio in active tag checks.

`--embed-lyrics`

Embed all available lyric sidecars before auditing. Every changed audio file is
then named in a `Lyrics embedded by --embed-lyrics` section, together with the
plain/timed lyric work performed, its backup, and confirmation that the file was
included in the following audit pass.

`--find-cover`

Resolve release artwork for audio that lacks an embedded Front cover. The
workflow uses an exact tagged MusicBrainz release ID first, then a conservative
MusicBrainz release search, and finally Discogs when `DISCOGS_TOKEN` is set.
Once a release is selected, every distinct available artwork part is
downloaded to the album folder—Front, Back, booklet, lyrics, inlay, disc/vinyl,
matrix, spine, obi, and other supplied types—but only the approved primary
Front image is embedded into audio. Every downloaded image is validated,
previewed, approved or rejected by one keypress, and followed by a re-audit.

`--no-color`

Disable ANSI styling.

`--unit-tests`

Run disposable generated-audio tests without scanning a music folder.

`-h` / `--help`

Show the styled usage screen.

## Examples

Pre-audit karaoke sidecar fix:

```bat
lrc2srt.py MiniLyricsFix --recursive --automatic-overwrites
```

Run that from the batch root before `audit_music_batch.py`. It creates missing
matching `.srt` sidecars only when a timestamped `.lrc` sidecar and `.txt` sidecar
already exist. Untimed/no-cue LRC files are skipped, leaving songs without
usable karaoke timing for the later lyric/karaoke workflow.

From the root of a batch, explicitly pass `.`:

```bat
audit_music_batch.py .
```

That prints the audit and then prompts through findings that have concrete,
implemented actions. `Y` applies the displayed action immediately; `N` skips it.
Running `audit_music_batch.py` without a folder or flags displays the styled
usage screen and performs no audit.

Or with an explicit folder:

```bat
audit_music_batch.py C:\soulseek\READY-FOR-TAGGING-AND-TRANSCRIBED
```

Write full reports:

```bat
audit_music_batch.py . --write-reports
```

Run report-only without prompts:

```bat
audit_music_batch.py . --no-interactive --write-reports
```

Find missing covers and retain the complete release artwork set:

```bat
audit_music_batch.py . --find-cover
```

Album tracks are grouped so the artwork set is downloaded once and the
approved Front cover is embedded into every affected track. An exact tagged
MusicBrainz release ID can proceed under the flag's explicit authorization.
Any search result that is not an exact tagged release still requires a separate
default-No release-identity confirmation before artwork is downloaded.

Run the self-contained generated-audio safety tests:

```bat
audit_music_batch.py --unit-tests
```

Unit-test mode uses disposable temporary audio and exits before scanning or
modifying any music batch. It reports 59 independently named tests so positive
and negative cases appear as separate pass/fail results. Coverage includes:

- complete and incomplete metadata, ReplayGain, comments, and genre rules
- plain lyrics, timed karaoke, instrumentals, timed/untimed sidecars, and embedding
- missing, single, multiple, sidecar-less, front/back/disc artwork; mocked exact
  and fuzzy cover lookup; invalid downloads; full artwork-set naming;
  release-level download deduplication; and image approve/reject/view behavior
- self-contained ANSI and Sixel preview generation, rejected-art naming, and
  Recycle Bin routing
- zero-byte media, cleanup candidates, kept backups/logs/markers, and TODOs
- active versus archived audio, archive repairs, duplicate formats, and filenames
- grouped album-artist filename cleanup, table output, playlist rewriting,
  collision refusal, and post-rename re-auditing
- immediate actions, path-containment safety, prompt behavior, and CLI usage

The album-write and blank-Enter tests share a folder named
`audit_music_batch-testdata-YYYYMMDDHHMMSS` under the system temporary folder.
The folder is sent to the Recycle Bin after the test class finishes.

The default interactive pass uses capitalized defaults:

- `[Y/n]` means `Y` approves, `N` rejects, and Enter approves by default.
- `[y/N]` means `Y` approves, `N` rejects, and Enter rejects/skips by default.

`Y` and `N` take effect from a single keypress; they do not require Enter. The
capitalized default choice is bright/bold and the lowercase non-default choice
is faint. The indented approval question begins with `❓`, uses urgent bright
orange styling, italicizes important nouns, and blinks while waiting at an
interactive terminal. It names the exact operation it will perform—for
example, “Extract the embedded artwork to an image sidecar now?” or “Embed the
timed karaoke lyrics into this audio file now?” Once a valid answer is received,
that same line is erased and immediately redrawn without blinking. The
`[Y/n]`/`[y/N]` block is replaced by a colored `Yes!` or `No!`, followed by
ANSI erase-to-end-of-line so no characters from the longer waiting prompt
remain onscreen. Prompts use ANSI styling by default. Use `--no-color` if a
terminal displays ANSI escape codes literally.

## Dependencies

Before scanning any music, the script runs a dependency preflight covering:

- `mutagen` for audio/tag inspection and metadata, lyric, and artwork writes
- Pillow for artwork-dimension checks, downloaded-image validation, safe JPEG
  normalization, and the self-contained ANSI/Sixel preview renderers
- `send2trash` for approved Recycle Bin cleanup
- `claire_progressbar` for long enumeration/audit progress
- `metamp3` and `metaflac` for ARGT-equivalent ReplayGain repairs
- `flac` and `ffmpeg` when `--unit-tests` needs generated FLAC/MP3 fixtures

Cover lookup uses Python's standard HTTPS client, so it does not require the
third-party `requests` package. MusicBrainz/Cover Art Archive lookup works
without a secret. Discogs is an optional final fallback and is enabled only
when the `DISCOGS_TOKEN` environment variable contains a token.

Chafa is optional. When `chafa` is on PATH or `C:\util\Chafa.exe` exists, it is
used for artwork previews. Without it, the script itself produces the same
review capability using a built-in 64-color Sixel encoder on a Sixel-capable
terminal or full-color ANSI half-blocks everywhere else. No binary is silently
downloaded or installed.

The `V` review key prefers `openimage.bat`. Because Claire's launcher uses
TCC-specific syntax, the script invokes it through TCC when available;
otherwise it duplicates the launcher's effective action by starting IrfanView
directly. If neither route can find an image viewer, dependency preflight warns
that the `V` key is unavailable and points to `IMAGE_VIEWER_EXECUTABLE` in the
`USER CONFIGURATION` section near the top of `audit_music_batch.py`.

Every missing tool is shown as a warning with the exact capability it disables.
Interactive mode then asks `❓ Proceed with the audit despite these missing
tools? [y/N]`; No is the safe default and cancels before scanning any music.
`--no-interactive` cannot ask a question, so it prints the same warnings and
continues with those capabilities unavailable.

The script will try the local `.codex_tools\python` helper folder used by this
sandbox before deciding that a Python dependency is unavailable. If the shared
progress module is missing, the audit can still proceed without a progress bar
after approval rather than crashing during import.

## Outputs

The terminal report is intentionally summarized:

- double-height section headers begin with sparkle/asterisk decoration
- audit root and active-audio/file totals use double-height colored lines
- “Findings by severity” and “Review needed” use double-height headings
- “Actions available for your approval” uses a double-height yellow warning
  gradient
- a completely clean audit ends with an undecorated, unindented double-height
  green confirmation line
- section headings use sparkle/asterisk decoration
- severity counts include a plain-language explanation of each level
- backup, JSON, log, and user-marker files are reported as right-aligned kept totals
  rather than long individual filename lists
- only actionable or manually reviewable findings list paths
- listed paths are faint and italic, with stable slight RGB variations that
  separate adjacent filenames visually; every audio filename begins with `♪`
- grouped Before/After filename cells wrap independently to the terminal width;
  continuation lines retain faint italics and use a slightly varied RGB shade
- report indentation uses four-space stops
- warning/review headings and missing-album labels use bright yellow
- displayed finding messages begin with `⚠️`, while every suggestion begins
  with an emoji chosen for lyrics, artwork, ReplayGain, metadata, cleanup, or
  archive work
- finding headings also use semantic icons; artwork failures, for example,
  begin with `🎨`
- approval-action labels are bright yellow before the em dash and their warning
  explanations are darker yellow after it; interactive action headings use the
  same yellow warning family
- suggestion lines are faint, darker cyan, and retain their category-specific
  emoji so they remain identifiable without competing with the warning
- successful writes separate subdued light-grey `💾 Backup:` details from the
  green `✅ Applied:` result and the explicit `🔁 Re-audit: passed` status
- cover discovery narrates source matching, downloads, validation, preview
  mode, approval/rejection, saved artwork, Front-only embedding, and re-audit
- rejected downloads are reported under their
  `rejected-by-username` name before they enter the Recycle Bin
- every interactive input prompt begins with `❓`, uses urgent orange styling,
  and italicizes its important nouns; the selected/default `Y` and `N` styling
  remains independently color-coded
- every colored header uses a per-character RGB fade; “Other files detected”
  is double-height bright-cyan through bright-blue, while review warnings fade
  from bright yellow to deeper yellow
- long labeled paths are split before DEC double-height rendering using
  `bigecho.bat`'s half-terminal-width and ten-column safety-margin rule, so the
  top and bottom halves can never wrap at different positions

The original progress timing was calibrated from five read-only passes over a
real 396-file batch. Median runtime was `0.5601054` seconds (`707.0098` files
per second). The deliberately early display threshold is now **600 files**, so
the bar appears before the measured one-second point instead of waiting until
708 files. This timing decision lives in
`audit_music_batch.py`. Rendering is delegated to
`C:\clairecjs_utils\claire_progressbar.py`, whose bar cycles through a bright
HSV rainbow by default; Python callers can pass `rainbow=False` to use ordinary
`tqdm` coloring. The shared library deliberately contains no timing,
throughput, or “slow enough” policy.

`collect_files()` now feeds that same bar. It appears as soon as discovery
reaches 600 files or actually takes more than one second, backfills the files
already found, then switches to a known combined enumeration/audit total.
Enumeration uses explicit, comma-formatted labels—`files found`, `elapsed`, and
`files/s`—rather than `tqdm`'s compact unknown-total notation. The shared
progress library inserts a space before every displayed unit, so output never
runs a number and unit together as `11933file`.
`--embed-lyrics` uses the same collection pass and the same continuous bar
instead of collecting the tree twice. Phase labels distinguish lyric embedding,
filesystem, duplicate/archive, and audio-tag work; the current audio filename
is displayed before it is opened. The shared bar uses a 0.05-second minimum
refresh interval, a 0.5-second maximum interval, and one update per refresh
opportunity so large batches do not appear stalled.

With `--write-reports`, the script writes these files to the audited folder
unless `--output-dir` is provided:

- `audit_music_batch_report.json`
- `audit_music_batch_report.md`
- `audit_music_batch_report.txt`

Interactive mode does not write a deferred approval plan. Approved actions are
performed immediately. Findings that require missing information or subjective
judgment remain in the report but are not presented as executable prompts.
Missing album tags are the exception: the auditor asks for an album value.
Entering text writes and verifies the tag; pressing Enter on a blank prompt
leaves the file unchanged.

## Recovery Safety

The auditor never permanently deletes an approved cleanup item. It uses the
operating system's Recycle Bin through `send2trash`; if recycling is unavailable
or fails, the action fails instead of falling back to `unlink`, `rmtree`, or
another permanent deletion.

Before changing an existing file's contents or embedded metadata in place, the
auditor creates and verifies a sibling backup using this exact pattern:

```text
whatever.txt.bak.202601131231.replaced-by-chatgpt.bak
```

This covers album-tag writes, plain/timed lyric embedding, artwork embedding,
existing `attrib.lst` repairs, and replacement of existing generated reports.
If the backup name already exists, the auditor retains both by adding
` (1)`, ` (2)`, and so on before the final `.bak`. New artwork sidecars use the
same collision style, such as `cover (1).jpg`; they are never silently
overwritten.

## Cover Finding and Complete Artwork Sets

When an audio file lacks an embedded cover, interactive mode always offers a
concrete choice. If local Front artwork exists, `Y` embeds it as before. If no
local Front exists, `Y` invokes the same conservative discovery workflow as
`--find-cover`: identify the release, obtain its artwork set, preview every
image, save every approved part, embed only Front, and immediately re-audit the
affected audio.

Resolution is deliberately ordered from strongest evidence to weakest:

1. An exact MusicBrainz release ID already embedded in the audio tags.
2. The tagged MusicBrainz release group's Front image, when the exact release
   has no Front.
3. A fielded MusicBrainz release search using album, album artist, date, track
   count, and release format.
4. Discogs only when `DISCOGS_TOKEN` is configured.

The MusicBrainz client identifies itself and spaces API requests to respect the
service's one-request-per-second application limit. An exact tagged release
does not need a second identity prompt after the user has approved the action
or explicitly supplied `--find-cover`. A search/fallback candidate is shown
with source, artist, release, date, formats, track count, and confidence, then
requires its own default-No identity approval. In `--no-interactive` mode,
non-exact candidates are skipped because their identity cannot be confirmed
safely.

After release selection, the workflow downloads every distinct image exposed
for that release—not just the cover. Common filenames are:

- primary Front: `cover.jpg`
- Back: `back.jpg`
- Booklet: `booklet.jpg`, or `lyrics.jpg` when its description identifies
  printed lyrics
- Liner/Inlay: `inlay.jpg`
- Medium: `disc.jpg`, `vinyl.jpg`, or `cassette.jpg` according to the release
  format
- Matrix/Runout: `matrix.jpg`
- Spine, obi, tray, poster, sticker, panel, or another supplied type: a matching
  descriptive `.jpg` name

Repeated types receive `-2`, `-3`, and so on. A collision with an existing
filesystem entry receives ` (1)`, ` (2)`, and so on; existing art is never
overwritten. In recognized album folders, these names live at album scope.
Loose/MISC audio uses same-name artwork so unrelated singles do not share art.

Every response is size-limited and checked for an image content type. Pillow
must decode it successfully; tiny images and implausibly shaped Front images
are rejected. Accepted candidates are normalized to high-quality JPEG before
review.

During an interactive run, each image gets a terminal preview and a single-key
`[A/r/v]` decision:

- `A` or Enter approves the image.
- `R` rejects it.
- `V` opens it through `openimage.bat`/IrfanView, then returns to the same
  approval question.

With the deliberately unattended combination
`--no-interactive --find-cover`, only exact tagged release IDs can proceed and
the explicit flag authorizes their images without terminal previews. A fuzzy
identity is never auto-approved.

Chafa supplies Sixel or full-color ANSI output when installed. Without Chafa,
the script's own renderer emits Sixel when the terminal advertises support and
ANSI half-block art otherwise. Set `AUDIT_MUSIC_ART_PREVIEW=sixel` to force
Sixel or `AUDIT_MUSIC_ART_PREVIEW=ansi` to force the portable ANSI renderer.

All three renderers read the live console width and height for every image.
They subtract the normal 12-column indent, a two-column right margin, and seven
rows reserved for preview status, the `[A/r/v]` question, and a possible
IrfanView message. The artwork is then enlarged or reduced without distortion
to occupy the largest possible portion of every remaining console cell. There
is no fixed `72x24` preview cap. Very small terminals automatically reduce the
indent and reserve while preserving room for both image and prompt.

Before recycling a rejected download, the script renames it to include
`rejected-by-username`, for example
`back.rejected-by-username.jpg`. Rejection never calls permanent deletion.
Rejecting a non-Front image skips only that part; rejecting Front aborts all
embedding for that release. The selected Front is the only image embedded, and
each audio file is backed up first. Album tracks share one downloaded artwork
set, and all affected tracks are re-audited after embedding.

The workflow does not ask an AI to guess from arbitrary image-search results.
Its confidence comes from structured release identifiers and metadata; fuzzy
or fallback identities remain human-approved.

For a recognized `Artist\YYYY - Album\` directory, repeated filename prefixes
such as `10-babymetal-pa_pa_ya.flac` are detected only when at least two audio
tracks share the pattern. The audio files and matching TXT/LRC/SRT/image/JSON/log
sidecars become one album-level finding, not separate prompts. Before approval,
the terminal prints every proposed name in aligned `Before filename` and
`After filename` columns. Long names wrap inside their own columns, with a
slightly different faint RGB shade on each continuation line. One default-No
prompt approves or rejects the entire group.

The proposed name removes the redundant artist and uses a track-number
underscore: `02_Da da dance (feat Tak Matsumoto).flac`. Albums with fewer than
ten distinct track numbers drop the leading zero (`2_Title.flac`); albums with
ten or more retain two digits (`02_Title.flac`). Underscores inside the title
become spaces, repeated whitespace is collapsed, and `feat.` is normalized to
`feat` without the period. The same basename is used for matching sidecars.

Approval preflights every source and destination before moving the first file.
Any collision aborts the whole group unchanged. Local M3U/M3U8 references are
backed up with the standard `replaced-by-chatgpt` filename, rewritten using
their original text encoding, and restored if a later operation fails. After
the grouped rename, the album is re-audited and the action fails unless the
redundant-artist finding has disappeared. A successful prompt prints that
re-audit as its own `🔁 Re-audit: passed` line. Generic organizational
directories such as `MISC` and `Various Artists` are not treated as artist
names.

When usable TXT/LRC/SRT sidecars exist but lyrics are not embedded, the finding
states that the sidecar exists, reports how many usable lyric/timestamped lines
it contains, and prints its exact path on a `📄 Confirmed sidecar:` line. It
also explicitly mentions `--embed-lyrics`, and interactive mode offers a
default-yes `Y/n` repair. If a sidecar exists but contains no usable lyric text
or timestamps, it is instead shown as `📄 Sidecar needs repair:` and no
executable approval is offered. If no sidecar exists, the message explicitly
says that none was found. After an approved write, the audio file is re-audited
immediately; the action is failed if the corresponding missing-lyrics finding
remains.

Sidecar lookup replaces the audio extension exactly once, so periods inside a
track name—such as `(feat._Artist).flac`—cannot truncate the sidecar stem.

The former `process_ready_batch.py` and `test_music_lyrics.py` sidecars are not
part of this workflow. Batch processing and generated-audio tests are contained
in `audit_music_batch.py`; run the latter with `--unit-tests`.

The filesystem/audio pass also detects suspiciously tiny audio, the Windows
read-only attribute, noncanonical parenthesized filename markers, and
multichannel audio. ReplayGain tags are validated on multichannel files rather
than skipped, so 5.1 and 7.1 files are not exempt from gain/peak checks.

Approving a missing-ReplayGain finding runs a portable Python reproduction of
Claire's `argt` / `add-ReplayGain-tags.bat` workflow on that track's immediate
folder:

1. Discover all immediate-child MP3 and FLAC files; the operation is
   intentionally non-recursive, like `argt`.
2. Back up every MP3 before modification.
3. Create the protective `ohhhh` sequester directory, move all MP3s into it,
   emit a random bright foreground color, and run
   `metamp3 --replay-gain *.*`.
4. Move every sequestered item back with collision-safe names and send the empty
   sequester directory to the Recycle Bin.
5. For each FLAC, emit a new random foreground/background pair, show its
   checkbox/filename, create and verify its backup, and run
   `metaflac --add-replay-gain <file>`.
6. Restore the original BAT workflow's final bright-red-on-black color and
   re-audit every audio file in the batch so already-fixed findings are skipped.

The subprocesses inherit the live console: their stdout and stderr are never
captured during an approved interactive action. `--no-color` suppresses random
ANSI colors but does not suppress tool output. Missing `metamp3` or `metaflac`
is reported before the corresponding audio format is modified.

## Finding Types

- `problem`: something is actively wrong and should be resolved before the batch
  is considered clean.
- `safe_fix`: likely-safe metadata or workflow fix, such as missing ReplayGain,
  missing embedded art when sidecar art exists, URL-only comments, or punk-family
  genre simplification.
- `safe_cleanup`: likely-safe junk cleanup, such as bare `__` files, temp BATs,
  `.m3u8`, `.xmp`, or VAD scratch SRTs with finished sidecars.
- `ask_first`: judgment call; prompt the human.
- `never_default`: keep by default. This includes `.bak` files.
- `info`: useful context that should not normally become an action.

## Guardrails

- Never default-delete `.bak` files.
- Never default-delete zero-byte `__ something __` marker/comment files.
- Do not treat log files as default-delete.
- Matching MP3/FLAC deprecation must preserve MP3-only sidecars before the MP3
  is deprecated.
- Archive folders containing audio should have the standard do-not-play
  `attrib.lst` line and the standard archival marker file.
- For merged tracks where only one section is instrumental/no-lyric, use
  section-specific hints like `[semi-instr] [no-lyr]`; do not mark the whole
  active filename `[instrumental]` or `[no lyrics]`.

## What It Audits

- active TODO filenames, excluding `completed-todos.log`
- missing/empty genre tags
- punk-family genre tags that can usually collapse to `Punk`
- URL-only comments that should become URL tags
- missing ReplayGain
- missing embedded cover art
- FLACs with embedded art but no obvious sidecar art
- missing embedded plain lyrics for non-instrumental/non-no-lyrics tracks
- missing embedded timed karaoke for non-instrumental/non-no-lyrics tracks
- present-but-unusable plain or timed lyric sidecars, distinguished from tracks
  with no corresponding sidecar
- missing SRT sidecar when matching LRC and TXT sidecars already exist
- unsynced-only embedded lyrics
- timestamped LRC sidecars that are not embedded as synced lyrics
- matching MP3/FLAC pairs in the same folder
- artist names redundantly repeated after track numbers throughout a recognized
  `Artist\YYYY - Album\` folder
- active WAV files
- unsupported audio formats
- zero-byte media/lyric/art files
- temp transcription files, VAD scratch files, `.m3u8`, `.xmp`
- archive/do-not-play folder compliance

For missing embedded covers, detection and execution share the same candidate
rules. A same-name image or `cover`, `folder`, or `front` image is preferred.
As in `embed-album-art-recursively-if-there-is-only-1-image-in-the-folder.bat`,
a folder's sole plausible image can also be embedded even when it has an
album-specific filename. A sole explicitly non-front image such as `back.jpg`
or `disc.jpg` is never promoted to the embedded cover. If no usable local image
exists, the prompt explicitly offers to search for the release artwork,
download and review every selected image part, embed only the approved Front,
and re-audit.

## Metadata Conventions

- Featured artists stay in the artist string, using lowercase `feat`: `Main
  Artist feat Guest`.
- Use that same full string for `artist` and `albumartist` on loose
  singles/MISC tracks.
- Keep the `title` clean: do not add `(feat Guest)` to the title unless the
  release title itself is an explicit version/remix label.

## Non-Goals

This script does not use AI image search, choose arbitrary web images, listen
to audio, merge tracks, or delete backups. It is read-only when no write action
is approved and neither write flag is supplied. `--embed-lyrics` embeds
matching TXT/LRC/SRT lyric-sidecar material (and may derive missing TXT/LRC
sidecars). `--find-cover` performs the structured, confirmation-gated
MusicBrainz/Cover Art Archive and optional Discogs artwork workflow described
above.
