# audit_music_batch.py

`audit_music_batch.py` audits incoming music batches for:

- missing or questionable title, artist, album, genre, comment, and URL tags
- missing ReplayGain track gain/peak tags
- leading, internal, or trailing silence longer than the configured threshold
- missing, multiple, or sidecar-less embedded cover artwork, with optional
  conservative release-art discovery
- missing or stale embedded plain lyrics/timed karaoke on vocal tracks
- unsupported audio formats and matching MP3/FLAC duplicates
- redundant artist prefixes, track separators, title capitalization, and
  matching audio/sidecar/backup filename families
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

Its interactive workflows also provide full-console Chafa/Sixel/ANSI artwork
previews with live resize re-rendering, original-image viewing through
`openimage.bat`/IrfanView, complete release-art-set downloads with Front-only
embedding, parallel waveform pre-render/review, excessive-silence detection,
timestamped backups, immediate post-write re-auditing, rainbow progress bars,
and More-style single-key paging.

## Flags

`--no-interactive`

Suppress action prompts. Automatic lyric/karaoke embedding still follows its
configured default. Missing-cover downloads are skipped because downloaded
images cannot be reviewed. Add `--no-embed-lyrics --no-find-cover` for a
strictly report-only run.

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

`--embed-lyrics` / `--no-embed-lyrics`

Force automatic validated plain-lyrics **and** timed-karaoke sidecar embedding
on or off together for this run. “Lyrics” in these option names is the umbrella
term; enabling lyric embedding always includes karaoke, and suppressing it
suppresses both. The built-in default is on and can be changed with
`--configure-defaults`. Every changed audio file is then named under an
`Embedding lyrics & karaoke into file:` line, together with the plain/timed work
performed, the shortened backup filename, and confirmation that the file was
included in the following audit pass.

Hash-prefixed transcription-generator comments are metadata, not lyrics. Lines
whose lyric text begins with `#` are excluded from TXT, LRC, and SRT-derived
plain/timed payloads and are never inserted into FLAC or MP3 tags. The source
sidecars themselves are left unchanged. Source selection is based on usable
content rather than extension alone: an empty or comment-only LRC cannot shadow
a same-basename SRT containing valid timestamps. In that case the SRT directly
supplies the embedded timed lyrics and the unusable LRC remains untouched.

The automatic pass compares normalized sidecar payloads with the embedded
copies and also compares sidecar/audio modification times. It refreshes an
embed when content differs or a sidecar was regenerated after the last audio
write. An exact, older-or-equal match is a no-op: it does not rewrite the audio
or create another backup.

`--refresh-embedded-lyrics`

Explicitly force-refresh both embedded plain lyrics and timed karaoke from every
available validated sidecar, even when the currently embedded payload is already
identical and no sidecar timestamp is newer. This option implies
`--embed-lyrics`, creates the normal verified backup for every audio file it
refreshes, narrates each plain/karaoke update, and re-audits afterward. It is
mutually exclusive with `--embed-lyrics` and `--no-embed-lyrics` because it is
the forced form of the same combined operation.

`--find-cover` / `--no-find-cover`

Force automatic missing-cover lookup on or off for this run. The built-in
default is **off**. A usable local `cover.*`, `folder.*`, or exact
same-basename image for an unnumbered/MISC track always takes priority: it is
previewed and offered for embedding without a network lookup.
`--find-cover` resolves release artwork only when the audio lacks both an
embedded Front cover and a usable local Front sidecar. The workflow uses an exact tagged
MusicBrainz release ID first, then searches Bandcamp alongside conservative
MusicBrainz release matches, and finally Discogs when `DISCOGS_TOKEN` is set.
Strong Bandcamp matches use the original-resolution release image from
Bandcamp's artwork CDN.
Once a release is selected, every distinct available artwork part is
downloaded to the album folder—Front, Back, booklet, lyrics, inlay, disc/vinyl,
matrix, spine, obi, and other supplied types—but only the approved primary
Front image is embedded into audio. Every downloaded image is validated,
previewed, approved or rejected by one keypress, and followed by a re-audit.

`--check-silence` / `--no-silence-check`

Force automatic excessive-silence analysis on or off. The built-in default is
on.

`--silence-threshold SECONDS`

For this run, flag only silence strictly longer than this value. The built-in
default-default value is `10.0` seconds.

`--review-waveforms` / `--no-review-waveforms`

Run only the interactive waveform-diagnostic workflow. It does not perform
metadata, lyrics, cover, ReplayGain, cleanup, or automatic filename auditing.
If no folder is supplied, it reviews the current folder; both of these are
equivalent:

```bat
audit_music_batch.py --review-waveforms
audit_music_batch.py . --review-waveforms
```

After an ordinary interactive audit finishes, the script gives one default-No
prompt offering to begin this waveform workflow immediately for the same root.
`--no-review-waveforms` (also accepted as `--no-waveform-review`) suppresses
that final offer completely. `--review-waveforms` remains the direct
waveform-only mode.

Each waveform is a disposable preview used to inspect the audio for excessive
silence, clipping or flattened peaks, dropouts, channel imbalance, and other
suspicious shapes. `N` means the waveform is fine and advances, `Y` records a
problem, `P` previews the audio, `E` opens the audio in the discovered editor,
and `V` opens the waveform image full-screen. Audio preview runs synchronously
through the neighboring legacy-named `play_wav_file.py`, then returns to the
same waveform question. Left and right arrows seek five seconds; Shift+left and
Shift+right seek fifteen seconds. Escape, `X`, `Q`, Ctrl+W, Alt+F4, Ctrl+C, or
Ctrl+Break stops preview playback. Despite its filename, the player uses
FFplay and supports WAV, FLAC, MP3, and other FFmpeg-decodable audio. After `Y`,
separate default-No prompts offer to edit the audio and to rename the audio file
to flag the problem.

### Bake ReplayGain into the audio (`B`)

During waveform review, when a usable nonzero ReplayGain track-gain tag exists,
`B` offers to bake that
loudness adjustment into the audio itself so players that ignore ReplayGain
receive approximately the same loudness. Positive gain is capped at the
measured peak headroom to prevent clipping; the prompt shows both the requested
and safely applied values whenever they differ. FLAC PCM is adjusted and
losslessly re-encoded. MP3 is decoded and re-encoded with FFmpeg/LAME's
highest-quality VBR setting, which is necessarily lossy; the prompt states this
before approval. In both cases, the original is retained as a verified
timestamped backup, artwork and metadata are preserved, and ReplayGain is
calculated again from the changed audio. After processing, the original blue
waveform is shown once more as a comparison only, without asking a question.
The replacement waveform is then rendered in green and shown immediately for
another review decision. The narration states the old tagged correction, the
amount baked into the samples, and the replacement file's freshly calculated
ReplayGain correction.

When the full tagged correction can be baked safely, the fresh ReplayGain value
should be approximately `+0.00 dB`. A player that honors ReplayGain and one that
ignores it should therefore produce approximately the same loudness from the
replacement file. If a positive correction is limited to prevent clipping, the
fresh tag retains the unapplied remainder: a tag-aware player can still reach
the target, while a tag-ignorant player remains quieter by that remainder.

The staged replacement is installed atomically when the volume permits it. If
Windows reports `Access is denied` because that volume allows file writes but
denies destination delete/rename access, the script falls back to a flushed
in-place write, verifies the complete result against the staged file with
SHA-256, and sends the staging file to the Recycle Bin. The already verified
timestamped original remains available throughout either route.

This is loudness correction based on the existing ReplayGain analysis, not
peak normalization to an arbitrary percentage. `B` is an interactive waveform
review control rather than a standalone command-line flag.

An `N`/fine decision is remembered in the per-user SQLite database
`%LOCALAPPDATA%\audit_music_batch\waveform_reviews.sqlite3`. A future review
skips that audio before scheduling any FFmpeg or terminal-preview work when its
normalized full path, byte size, and nanosecond modification time are all
unchanged. Editing, replacing, or moving the audio invalidates that approval
and makes it reviewable again. When the database exceeds 50 MiB, startup removes
records for files that no longer exist and compacts the database.

`--waveform-workers NUMBER`

Use 1 through 8 concurrent `ffmpeg` workers to pre-render the entire remaining
waveform queue while one full-screen preview is being reviewed. The default is
8 workers. A second bounded pool also converts upcoming JPEGs into
display-ready Chafa/Sixel/ANSI payloads, keeping up to twice the configured
worker count ready ahead without allowing a very large batch to consume
unbounded memory.

`--configure-defaults` / `--show-defaults`

Interactively persist or display automatic lyric, cover, and silence behavior
beside the installed script. The config file is created only by
`--configure-defaults`; ordinary runs and installations do not create it.

`--no-pager`

Disable the automatic More-style single-key pause used in a real console.

`--no-color`

Disable ANSI styling.

`--unit-tests`

Run disposable generated-audio tests without scanning a music folder.

`-h` / `--help`

Show the styled usage screen.

## Examples

The command used for a missing-karaoke-sidecar repair is:

```bat
lrc2srt.py MiniLyricsFix --recursive --automatic-overwrites
```

When the audit finds at least one timestamped `.lrc` plus matching `.txt` but
no matching `.srt`, interactive mode offers to run that exact command from the
batch root. The prompt defaults to Yes, streams the converter output, runs the
recursive repair once for the batch, and re-audits the affected tracks. Its
legend deliberately omits `F=Do All in Folder`, because the command already
operates recursively over the entire audited batch root.
Untimed/no-cue LRC files are skipped, leaving songs without usable karaoke
timing for the later lyric/karaoke workflow.

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
audit_music_batch.py . --no-interactive --no-embed-lyrics --no-find-cover --write-reports
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

Force-refresh both plain lyrics and timed karaoke from current sidecars:

```bat
audit_music_batch.py . --refresh-embedded-lyrics
```

This deliberately rewrites every audio file that has at least one usable
plain-lyrics or timed-karaoke source, even if its current embed is already
identical. Use ordinary `--embed-lyrics` for the smarter missing/stale-only
behavior.

Review only waveforms, with three background render workers:

```bat
audit_music_batch.py . --review-waveforms --waveform-workers 3
```

Override the excessive-silence threshold for one normal audit:

```bat
audit_music_batch.py . --silence-threshold 15
```

Change or inspect persistent automatic behavior:

```bat
audit_music_batch.py --configure-defaults
audit_music_batch.py --show-defaults
```

Run the self-contained generated-audio safety tests:

```bat
audit_music_batch.py --unit-tests
```

Unit-test mode uses disposable temporary audio and exits before scanning or
modifying any music batch. It reports 98 independently named tests so positive
and negative cases appear as separate pass/fail results. Every test line starts
with a dynamically sized, right-aligned progress prefix such as
`[ 1/98] ➜`; in normal color mode, its brackets, bold current number, faint
total, darker slash, arrow, and subtly varied test description use distinct
colors. Coverage includes:

Unit-test mode always disables the More-style pager, even in an interactive
console. Output produced internally by a passing test is buffered so progress
bars, carriage returns, and erase-line sequences cannot overwrite that test's
numbered name; each successful case remains as one complete `... ok` line.

- complete and incomplete metadata, ReplayGain, comments, and genre rules
- plain lyrics, timed karaoke, instrumentals, timed/untimed sidecars, embedding,
  generator-comment exclusion, newer-sidecar detection, recursive default-Yes
  MiniLyricsFix SRT generation, and verified refreshes
- forced combined plain-lyrics/timed-karaoke refreshes, including flag
  implication, backup creation, narration, and post-refresh re-auditing
- missing, single, multiple, sidecar-less, front/back/disc artwork; mocked exact
  and fuzzy cover lookup; invalid downloads; full artwork-set naming;
  release-level download deduplication; and image approve/reject/view behavior
- self-contained ANSI and Sixel preview generation, rejected-art naming, and
  Recycle Bin routing
- zero-byte media, cleanup candidates, kept backups/logs/markers, and TODOs
- active versus archived audio, archive repairs, duplicate formats, and filenames
- grouped album-artist filename cleanup, table output, playlist rewriting,
  collision refusal, and post-rename re-auditing
- immediate actions, path-containment safety, invalid-key beeping without prompt
  duplication, prompt behavior, and CLI usage
- current-folder waveform invocation, full-width pixel geometry, a grey preview
  boundary, amplitude-honest peak scaling, measured waveform summaries,
  multi-row prompt erasure, editor/view/problem controls, grouped
  problem-file/sidecar/backup renaming, and disposable-only waveform staging
- immediate progress on small and large interactive audits, aligned wrapped
  audit-root paths, no-op grouped-rename rejection, compact inline album-folder
  display, and self-erasing default-No waveform handoffs
- progress-library discovery beside the script and in either
  `clairecjs_util` or `clairecjs_utils` subfolders

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
remain onscreen. Wrapped prompts count and erase every occupied console row,
so a long question is not left duplicated above its settled answer. When a
question plus its explanatory key legend would exceed the live console width,
the complete legend moves to a second line whose first character aligns with
the first word after `❓`; the terminal is never left to split that legend at an
arbitrary character. Prompts use ANSI styling by default. Use `--no-color` if a
terminal displays ANSI escape codes literally.

Unsupported keys never print another copy of the waiting prompt. They produce a
100 Hz, 0.2-second warning beep and leave the original blinking prompt exactly
where it is. Arrow keys and other extended console keys are rejected the same
way instead of being mistaken for Enter or a default answer.

Repeatable action prompts additionally show
`Y=Yes / N=No / A=Always / V=Never / F=Do All in Folder`.
`Always` and `Never` remember the decision for that action category for the
rest of the run. `Do All in Folder` approves the same category for the
current folder only. Remembered decisions are narrated without asking for
another keypress. Root-wide actions such as recursive MiniLyricsFix omit the
folder choice because they are not per-file operations. Album-tag value entry
remains per-file because it requires actual text, not a reusable yes/no
decision.

## Dependencies

Before scanning any music, the script runs a dependency preflight covering:

- `mutagen` for audio/tag inspection and metadata, lyric, and artwork writes
- Pillow for artwork-dimension checks, downloaded-image validation, safe JPEG
  normalization, and the self-contained ANSI/Sixel preview renderers
- `send2trash` for approved Recycle Bin cleanup
- `claire_progressbar` for long enumeration/audit progress
- `metamp3` and `metaflac` for ARGT-equivalent ReplayGain repairs
- `ffmpeg` for the default excessive-silence audit and waveform JPEG rendering
- `flac` and `ffmpeg` when `--unit-tests` needs generated FLAC/MP3 fixtures

Cover lookup uses Python's standard HTTPS client, so it does not require the
third-party `requests` package. HTTPS verification prefers the installed
`certifi` CA bundle and never disables certificate checking. A Cover Art
Archive certificate-validation failure is retried through that release's
verified Internet Archive `mbid-.../index.json` object; CAA image URLs have the
same direct Internet Archive fallback. MusicBrainz/Cover Art Archive lookup
works without a secret. Discogs is an optional final fallback and is enabled
only when the `DISCOGS_TOKEN` environment variable contains a token.

Chafa is optional. When `chafa` is on PATH or `C:\util\Chafa.exe` exists, it is
used at its highest accuracy setting for artwork previews. Without it, the
script itself produces the same review capability using a built-in 64-color
Sixel encoder on a Sixel-capable terminal or full-color ANSI half-blocks
everywhere else. No binary is silently downloaded or installed.

The `V` review key prefers `openimage.bat`. Because that launcher uses
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
- severity rows have category-specific emoji, right-justified labels immediately
  beside aligned colons, right-aligned counts, and a plain-language explanation
  of each level
- backup, JSON, log, and user-marker files have their own emoji and are reported
  as right-aligned kept totals rather than long individual filename lists
- action-result backups show only a subdued backup filename rather than a full
  path
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
  green `🔧 Applied:` result and the explicit unboxed-green
  `✔️ Re-audit: passed` status
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
- script-generated errors begin and end with `💥💥💥`; the bright-red
  `ERROR:` label blinks when ANSI styling is enabled
- long labeled paths are split before DEC double-height rendering using
  `bigecho.bat`'s half-terminal-width and ten-column safety-margin rule, so the
  top and bottom halves can never wrap at different positions

The original progress timing was calibrated from five read-only passes over a
real 396-file batch. Tag reads and automatic embedding can still take several
seconds on much smaller albums, so every interactive audit now starts an
indeterminate file-enumeration progress bar immediately and converts it to the
determinate audit bar as soon as the file total is known. Rendering is delegated
to
`claire_progressbar.py`, whose bar cycles through a bright HSV rainbow by
default; Python callers can pass `rainbow=False` to use ordinary `tqdm`
coloring. To remain portable when the script and library are copied together,
the loader checks beside `audit_music_batch.py`, then its
`clairecjs_util\` and `clairecjs_utils\` subfolders. The installed shared
library normally lives at `C:\clairecjs_utils\claire_progressbar.py`. The
library deliberately contains no timing, throughput, or “slow enough” policy.

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
is displayed before it is opened. Determinate audit bars omit the words
`checks` and `checks/s`; their compact throughput is formatted as `1.20/sec`,
and their middle-ellipsized filename preview is never longer than 16
characters. The silence phase is labeled simply `Silence detect`. The shared
bar uses a 0.05-second minimum
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

## WAV Conversion

Each active WAV is an approval-backed conversion option rather than a dead-end
warning. Approval creates a same-name FLAC, then renames the original WAV to
the standard timestamped `.bak.…replaced-by-chatgpt.bak` form, preserves
readable source metadata and conservative folder-derived title/artist/album/date
details, embeds usable lyric/karaoke sidecars, uses an existing approved Front
sidecar when present, or enters the normal cover-download/render/approval flow.
The newly created FLAC is re-opened and audited before the action reports
success. Existing FLACs are never overwritten.

When an audio file lacks an embedded cover, interactive mode always checks the
folder again immediately before prompting. If local `cover.*`, `folder.*`, or
an exact same-basename image beside an unnumbered/MISC track exists, the script
renders that exact image and asks whether to embed it; it does not search or
download anything. This local-preview action
also takes priority when `--find-cover` is active. Only when no usable local
Front exists does `Y` invoke the same conservative discovery workflow as
`--find-cover`: identify the release, obtain its artwork set, preview every
image, save every approved part, embed only Front, and immediately re-audit the
affected audio.

Before asking to embed an existing local `cover.*`, `folder.*`, or eligible
same-basename MISC image, the script renders that exact sidecar using the same
full-console Chafa/Sixel/ANSI preview system used for downloaded artwork. The
prompt follows the preview and still names the candidate explicitly, such as
`(folder.jpg)` or `(Ghosts -- I'm Baby (live).jpg)`.

When the auditor exports artwork already embedded in a FLAC or MP3 because the
folder had no matching sidecar (or the audio held multiple pictures), each
newly extracted image is likewise rendered and reviewed before it is kept.
Approve to retain it; reject to rename it with `.rejected-by-username` and send
it to the Recycle Bin. This prevents an incorrectly typed embedded picture from
quietly becoming a trusted `cover.jpg`, `back.jpg`, or other folder asset.
This sidecar-less embedded-art check applies equally to FLAC and MP3 files.

For numbered album-track filenames, extracted Front artwork is named
`cover.jpg` and the other typed parts use their normal folder names such as
`back.jpg` and `disc.jpg`. For a loose/MISC file with no leading track number,
the Front image is track-specific instead—for example `Ghosts (2023).jpg`—so
unrelated singles never overwrite one another's art. Artwork review prefers
the tuned Chafa Sixel renderer directly; ANSI symbols are only a fallback when
Sixel rendering itself cannot be used.

That matching same-basename MISC image is recognized on later audits as the
track's own Front-art candidate: it is previewed, approved, and embedded only
into that exact unnumbered audio file. It is never inferred to apply to another
file. Numbered album tracks still require album-scoped `cover.*` or `folder.*`.

Cover lookup does not run as a default startup phase. It begins only after an
explicit `--find-cover` or an approved missing-cover action. The double-height
header is `Finding cover art:` and is emitted only when at least one missing
cover will actually be handled. MusicBrainz release resolution and the
Bandcamp/MusicBrainz artwork search and download queue each use the shared
rainbow progress bar, so
network waits remain visibly active.

Resolution is deliberately ordered from strongest evidence to weakest:

1. An exact MusicBrainz release ID already embedded in the audio tags.
2. The tagged MusicBrainz release group's Front image, when the exact release
   has no Front.
3. Bandcamp search using album/track and artist, accepting only a strongly
   matching release and requesting its original-resolution Front image.
4. A fielded MusicBrainz release search using album, album artist, date, track
   count, and release format.
5. Discogs only when `DISCOGS_TOKEN` is configured.

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
Loose/MISC audio still receives the descriptive release-art files in its own
immediate folder; an exact same-basename image may be used only for its matching
unnumbered track.

Every response is size-limited and checked for an image content type. Pillow
must decode it successfully; tiny images and implausibly shaped Front images
are rejected. Accepted candidates are normalized to high-quality JPEG before
review.

During an interactive run, each image gets a terminal preview and the expanded
`[Y=Yes/Enter | N=No | R=Refresh | V=View original]` decision:

- `Y` or Enter approves the image.
- `N` rejects it.
- `R` re-renders the preview using the current console viewport.
- `V` opens the original image through `openimage.bat`/IrfanView, then returns
  to the same approval question.

With `--no-interactive`, all cover lookup/download work is skipped—even when
`--find-cover` is supplied—because neither release identity nor downloaded
images can be reviewed safely. Use interactive mode for cover acquisition.

Chafa supplies Sixel or full-color ANSI output when installed. Without Chafa,
the script's own renderer emits Sixel when the terminal advertises support and
ANSI half-block art otherwise. Set `AUDIT_MUSIC_ART_PREVIEW=sixel` to force
Sixel or `AUDIT_MUSIC_ART_PREVIEW=ansi` to force the portable ANSI renderer.

All three renderers read the live console width and height for every image.
While a Windows review prompt is waiting, the script polls the live viewport;
resizing the window or changing the console font size automatically triggers a
new render. `R` provides the same refresh explicitly. The renderers subtract
the normal 12-column indent, a two-column right margin, and seven rows reserved
for preview status, the expanded review question, and a possible IrfanView
message. The artwork is enlarged or reduced without distortion to occupy the
largest possible portion of every remaining console cell. There is no fixed
`72x24` preview cap. Very small terminals automatically reduce the indent and
reserve while preserving room for both image and prompt. ANSI-symbol sharpness
is limited by the number of terminal character cells, so a smaller console
font produces a sharper re-render; Sixel or `V=View original` remains the
highest-detail option.

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

## Silence and Waveform Review

Normal audits use `ffmpeg` to detect leading, internal, and trailing silence at
`-50 dB`. A finding is created only when one continuous interval is strictly
longer than the effective threshold; the built-in default-default is `10.0`
seconds. `--silence-threshold`, `--check-silence`, `--no-silence-check`, and
`--configure-defaults` control that behavior. The finding includes the
interval type, timestamps, and duration. In interactive mode it asks to open
the exact flagged audio file in the configured editor; Enter defaults to Yes
so an excessive-silence repair is not easy to skip accidentally. The separate
waveform-review workflow remains available for visual confirmation. Up to
eight silence decoders begin concurrently as audio files are discovered, while
enumeration and the other audit checks continue. Their results are harvested
later in deterministic filename order, avoiding a serial silence-analysis
pause at startup or at the end of the audit.

`--review-waveforms` performs only waveform diagnosis. It submits the entire
not-yet-approved audio queue to a bounded worker pool, so up to
`--waveform-workers` JPEGs render concurrently while the user reviews the
current full-width Sixel/ANSI preview. The default eight-worker queue starts
every JPEG job before review begins. Independently, a bounded look-ahead cache
prepares Chafa, built-in Sixel, or ANSI terminal output for the next 16 tracks
by default, so advancing normally emits an already converted payload instead
of synchronously invoking the renderer. If the window or font changes, the
cached geometry is discarded for that track and it is rendered again at the
new live size. The renderer re-reads the live viewport and Windows
console-font cell size for each uncached or resized preview. It begins at the same 12-cell
indent as the filename/status lines; the filename formatter's usual extra
one-cell list alignment is removed on this screen so its note begins at the
waveform's exact left edge. Chafa receives the explicit live view dimensions
and exact-dimensions stretch mode so a height-limited JPEG cannot leave unused
columns. The only unused horizontal cell is the deliberate one-cell right
margin. A faint grey box marks the waveform's exact top, bottom, left, and
right bounds, with matching faint grey dividers between every stacked audio
channel. An unboxed area at the right edge contains a grey amplitude axis and
five centered measurements: peak volume, average (RMS) volume, the current
ReplayGain correction in dB, its linear multiplier, and longest detected
silence. The measurements use a wider proportional font, with purple, blue,
mint, orange, and yellow numerical values. If the longest continuous silence exceeds
the effective threshold, that value alone turns red. If no ReplayGain
track-gain tag exists, both ReplayGain values read `n/a`.
Longest-silence seconds are truncated rather than rounded, so `9.9999` seconds
is displayed as `9s`; cumulative silence is not displayed.

The same FFmpeg decode that renders the picture measures every channel's actual
sample peak, RMS level, and silence intervals. Because FFmpeg's waveform picture
normalizes its drawing independently, the script rescales each stacked channel
to its measured absolute peak and an automatically selected vertical axis.
The axis ceiling is the next 5% step with a small amount of headroom: a 66%
peak uses a ±70% graph, 75% uses ±80%, and near-full-scale audio remains at
±100%. The top and bottom labels show that real axis limit, while `peak vol`
continues to report the actual measured peak. Labels are clamped inside the
image so the auto-zoom cannot crop them. A small cyan-only antialiasing pass widens
isolated true-peak columns enough to remain visible after JPEG and terminal
downscaling without changing their vertical amplitude. Short horizontal guides
and percentage labels appear only at the outer top and bottom axis limits;
none are repeated beside the middle channel divider. In the decision prompt,
the audio filename is faint and italic.

The controls answer a diagnostic question rather than asking whether to keep a
generated JPEG:

- `N` — no problem; the waveform looks fine and review continues
- `Y` — yes, there is a problem; record it and ask whether to edit or rename
- `E` — open the audio itself in Adobe Audition, Cool Edit, Audacity,
  ocenaudio, Sound Forge, or a configured editor
- `B` — bake the tagged ReplayGain loudness change into FLAC/MP3 audio, refresh
  the tags, and display a newly generated green waveform
- `V` — view the waveform JPEG full-screen through `openimage.bat`/IrfanView

For a waveform whose longest silence exceeds the effective threshold, the
screen shows a red warning and changes the legend to `ENTER/E=Edit audio`.
Pressing Enter therefore opens the audio editor by default; after the editor
opens, the review prompt remains available so the file can still be marked or
renamed.

When the `Y` follow-up rename is approved, an `rn.bat`-style editable filename
prompt starts with the current audio filename. The verified rename includes the
audio, matching same-stem lyric/log sidecars, old `.bak…` family members, and
local playlist references. Playlist content is backed up before replacement.

`AUDIO_EDITOR_EXECUTABLE` in the `USER CONFIGURATION` section or the
`AUDIT_MUSIC_AUDIO_EDITOR` environment variable can name a preferred editor.
Otherwise the script searches PATH, installed Adobe Audition directories, and
known local editor/launcher paths.

Waveform JPEGs are never copied beside the music. Their timestamped staging
directory is created under `C:\recycled` when that writable directory exists,
otherwise under `%TEMP%`, and remains there as disposable temporary material
until ordinary temporary-file cleanup. A track marked `Y` retains the exact
staged preview path in the review result. `N` never changes the audio; `Y` only
opens an editor or renames files when those separate follow-up prompts are also
approved.

Files marked fine are recorded only after the decision (and after any editor
round-trip). The results distinguish newly approved files from unchanged,
previously approved files that were skipped. This persistent approval database
uses Python's built-in SQLite support and never writes into the music folder.

## Album Filename Normalization

For a recognized `Artist\YYYY - Album\` directory, repeated filename prefixes
such as `10-babymetal-pa_pa_ya.flac` are detected only when at least two audio
tracks share the pattern. The audio files and matching TXT/LRC/SRT/image/JSON/log
sidecars become one album-level finding, not separate prompts. Before approval,
the terminal prints every proposed name in aligned `Before filename` and
`After filename` columns. Long names wrap inside their own columns, with a
slightly different faint RGB shade on each continuation line. One default-No
prompt approves or rejects the entire group.

The proposed name removes the redundant artist and uses a track-number
underscore: `02_Da Da Dance (feat Tak Matsumoto).flac`. Albums with fewer than
ten distinct track numbers drop the leading zero (`2_Title.flac`); albums with
ten or more retain two digits (`02_Title.flac`). Underscores inside the title
become spaces, ordinary title words are capitalized, accepted all-caps/mixed
case words are preserved, repeated whitespace is collapsed, and `feat.` is
normalized to `feat` without the period. The same basename is used for
matching sidecars and timestamped `.bak...replaced-by-chatgpt.bak` descendants.
An eight-character hexadecimal/underscore download-tracking token at the very
end of a title is also removed when it contains at least two digits, covering
suffixes such as `-E75E4EC6`, `-35876105`, and `-F45_CC0D` without stripping
ordinary final words. The same removal applies to audio, matching sidecars, and
timestamped backup descendants.
The Before/After table uses only the width its contents require and wraps only
when that natural width would exceed the live console viewport.

Approval preflights every source and destination before moving the first file.
Any collision aborts the whole group unchanged. Local M3U/M3U8 references are
backed up with the standard `replaced-by-chatgpt` filename, rewritten using
their original text encoding, and restored if a later operation fails. After
the grouped rename, the album is re-audited and the action fails unless the
redundant-artist finding has disappeared. A successful prompt prints that
re-audit as its own `✔️ Re-audit: passed` line. Generic organizational
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

Sidecar text decoding recognizes UTF-8, Windows-1252, UTF-16, and UTF-32,
including byte-order marks and strong BOM-less UTF-16 patterns. Consequently,
UTF-16 SRT files written by subtitle or lyrics tools retain their readable
`HH:MM:SS,mmm --> HH:MM:SS,mmm` timestamps and participate in the same
automatic timed-karaoke embedding workflow instead of being misreported as
unusable.

Already-embedded lyrics are not assumed current merely because the tags exist.
For both FLAC and MP3, the auditor compares the normalized embedded plain/timed
payloads with the usable sidecars. It also detects a sidecar modification time
newer than the audio, covering a transcription that was regenerated with
identical text. A single `Embedded lyrics need refreshing` finding lists the
affected sidecars and explains whether their content differs, they are newer,
or both. Interactive approval refreshes all affected lyric payloads with one
backup and immediately re-audits; the default automatic lyric pass performs the
same refresh before reporting.

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
the `argt` / `add-ReplayGain-tags.bat` workflow on that track's immediate
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
- embedded lyrics or karaoke that differ from their current sidecars, or whose
  sidecars were regenerated after the last audio write
- present-but-unusable plain or timed lyric sidecars, distinguished from tracks
  with no corresponding sidecar
- missing SRT sidecar when matching LRC and TXT sidecars already exist
- a newer manually edited MiniLyrics LRC that needs the matching SRT backfilled
  through `lrc2srt.py`; LRCs that merely derive from their SRT are left alone
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

For missing embedded covers, detection and execution share the same strict
candidate rules: a local `cover.*` or `folder.*` can become album Front art;
an exact same-basename image can become Front art only for its matching
unnumbered/MISC audio file. `proof.*`, `front.*`, unrelated same-name images, a
folder's sole arbitrary image, `back.*`, `disc.*`, and other artwork parts are
never promoted. An
approved non-JPEG Front candidate is converted to a collision-safe JPEG before
embedding. If no usable local Front exists, the prompt explicitly offers to
search for the release artwork, download and review every selected image part,
embed only the approved Front, and re-audit.

## Metadata Conventions

- Featured artists stay in the artist string, using lowercase `feat`: `Main
  Artist feat Guest`.
- Use that same full string for `artist` and `albumartist` on loose
  singles/MISC tracks.
- Keep the `title` clean: do not add `(feat Guest)` to the title unless the
  release title itself is an explicit version/remix label.

## Non-Goals

This script does not use AI image search, choose arbitrary web images, merge
tracks, or delete backups. Its default normal audit may embed validated
lyric/karaoke sidecars after creating backups; use `--no-embed-lyrics` to
suppress both parts of that behavior. `--refresh-embedded-lyrics` is the
explicit force-refresh form and likewise always handles plain lyrics and timed
karaoke together. Cover acquisition remains interactive and its built-in
default is off. For a strictly report-only run, use
`--no-interactive --no-embed-lyrics --no-find-cover`. `--find-cover` performs
the structured, confirmation-gated MusicBrainz/Cover Art Archive and optional
Discogs artwork workflow described above.
