# audit_music_batch.py

`audit_music_batch.py` audits incoming music batches for:

- missing or questionable title, artist, album, genre, comment, and URL tags
- missing ReplayGain track gain/peak tags
- missing, multiple, or sidecar-less embedded cover artwork
- missing embedded plain lyrics or timed karaoke on vocal tracks
- unsupported audio formats and same-stem MP3/FLAC duplicates
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

Embed all available lyric sidecars before auditing.

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
same-stem `.srt` files only when a timestamped `.lrc` and matching `.txt`
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

Run the self-contained generated-audio safety tests:

```bat
audit_music_batch.py --unit-tests
```

Unit-test mode uses disposable temporary audio and exits before scanning or
modifying any music batch. It reports 46 independently named tests so positive
and negative cases appear as separate pass/fail results. Coverage includes:

- complete and incomplete metadata, ReplayGain, comments, and genre rules
- plain lyrics, timed karaoke, instrumentals, timed/untimed sidecars, and embedding
- missing, single, multiple, sidecar-less, front/back/disc artwork
- zero-byte media, cleanup candidates, kept backups/logs/markers, and TODOs
- active versus archived audio, archive repairs, duplicate formats, and filenames
- immediate actions, path-containment safety, prompt behavior, and CLI usage

The album-write and blank-Enter tests share a folder named
`audit_music_batch-testdata-YYYYMMDDHHMMSS` under the system temporary folder.
The folder is sent to the Recycle Bin after the test class finishes.

The default interactive pass uses capitalized defaults:

- `[Y/n]` means `Y` approves, `N` rejects, and Enter approves by default.
- `[y/N]` means `Y` approves, `N` rejects, and Enter rejects/skips by default.

`Y` and `N` take effect from a single keypress; they do not require Enter. The
capitalized default choice is bright/bold and the lowercase non-default choice
is faint. Prompts use ANSI styling by default. Use `--no-color` if a terminal
displays ANSI escape codes literally.

## Dependencies

Full tag/art checks use `mutagen`. The script will try the local
`.codex_tools\python` helper folder used by this sandbox before reporting that
tag checks were skipped.

## Outputs

The terminal report is intentionally summarized:

- all double-height lines begin with sparkle/asterisk decoration
- audit root and active-audio/file totals use double-height colored lines
- “Findings by severity” and “Review needed” use double-height headings
- section headings use sparkle/asterisk decoration
- severity counts include a plain-language explanation of each level
- backup, JSON, log, and user-marker files are reported as right-aligned kept totals
  rather than long individual filename lists
- only actionable or manually reviewable findings list paths
- listed paths are faint and italic, with stable slight RGB variations that
  separate adjacent filenames visually
- report indentation uses four-space stops
- warning/review headings and missing-album labels use bright yellow
- every colored header uses a per-character RGB fade; “Other files detected”
  is double-height bright-cyan through bright-blue, while review warnings fade
  from bright yellow to deeper yellow
- long labeled paths are split before DEC double-height rendering using
  `bigecho.bat`'s half-terminal-width and ten-column safety-margin rule, so the
  top and bottom halves can never wrap at different positions

The progress threshold is calibrated from five read-only passes over a real
396-file batch. Median runtime was `0.5601054` seconds (`707.0098` files per
second), so the `tqdm` status bar first appears at 708 files—the first integer
count predicted to exceed one second. This timing decision lives in
`audit_music_batch.py`. Rendering is delegated to
`C:\clairecjs_utils\claire_progressbar.py`, whose bar cycles through a bright
HSV rainbow by default; Python callers can pass `rainbow=False` to use ordinary
`tqdm` coloring. The shared library deliberately contains no timing,
throughput, or “slow enough” policy.

Enumeration now feeds that same bar. It appears as soon as discovery crosses
the calibrated threshold or actually takes more than one second, backfills the
files already found, then switches to a known combined enumeration/audit total.
Phase labels distinguish filesystem, duplicate/archive, and audio-tag work; the
current audio filename is displayed before its tags are opened. The shared bar
uses a 0.05-second minimum refresh interval, a 0.5-second maximum interval, and
one update per refresh opportunity so large batches do not appear stalled.

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

When usable TXT/LRC/SRT sidecars exist but lyrics are not embedded, the finding
explicitly mentions `--embed-lyrics` and interactive mode offers a default-yes
`Y/n` repair. After an approved write, the audio file is re-audited immediately;
the action is failed if the corresponding missing-lyrics finding remains.

The former `process_ready_batch.py` and `test_music_lyrics.py` sidecars are not
part of this workflow. Batch processing and generated-audio tests are contained
in `audit_music_batch.py`; run the latter with `--unit-tests`.

The filesystem/audio pass also detects suspiciously tiny audio, the Windows
read-only attribute, noncanonical parenthesized filename markers, and
multichannel audio. ReplayGain tags are validated on multichannel files rather
than skipped: `rsgain` ReplayGain 2.0 uses `libebur128`/ITU BS.1770 for
multichannel analysis, so 5.1 and 7.1 files are not exempt from gain/peak checks.

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
- Same-stem MP3/FLAC deprecation must preserve MP3-only sidecars before the MP3
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
- missing SRT when same-stem LRC and TXT already exist
- unsynced-only embedded lyrics
- timestamped LRC sidecars that are not embedded as synced lyrics
- same-folder same-stem MP3/FLAC pairs
- active WAV files
- unsupported audio formats
- zero-byte media/lyric/art files
- temp transcription files, VAD scratch files, `.m3u8`, `.xmp`
- archive/do-not-play folder compliance

## Metadata Conventions

- Featured artists stay in the artist string, using lowercase `feat`: `Main
  Artist feat Guest`.
- Use that same full string for `artist` and `albumartist` on loose
  singles/MISC tracks.
- Keep the `title` clean: do not add `(feat Guest)` to the title unless the
  release title itself is an explicit version/remix label.

## Non-Goals

This script does not search the internet, pick album covers, listen to audio,
merge tracks, or delete backups. It is read-only by default. The explicit
`--embed-lyrics` option is the exception: it embeds available same-stem
TXT/LRC/SRT material (and may derive missing TXT/LRC sidecars) before auditing.
