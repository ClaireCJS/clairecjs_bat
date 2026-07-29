# audit_music_batch.py

`audit_music_batch.py` is a read-only proposal engine for incoming music batches.
It audits the current batch against the recurring workflow rules from
`C:\notes\audio-processing-batch-NOTES.txt` and produces reports/proposal codes
instead of silently changing files.

## Basic Usage

Pre-audit karaoke sidecar fix:

```bat
lrc2srt.py MiniLyricsFix --recursive --automatic-overwrites
```

Run that from the batch root before `audit_music_batch.py`. It creates missing
same-stem `.srt` files only when a timestamped `.lrc` and matching `.txt`
already exist. Untimed/no-cue LRC files are skipped, leaving songs without
usable karaoke timing for the later lyric/karaoke workflow.

From the root of a batch:

```bat
audit_music_batch.py
```

That prints the audit and then starts the attention-friendly approval prompt by
default.

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

The default interactive pass uses capitalized defaults:

- `[Y/n]` means Enter approves the proposal.
- `[y/N]` means Enter rejects/skips the proposal.

Prompts use ANSI color by default. Use `--no-color` if a terminal displays ANSI
escape codes literally.

## Dependencies

Full tag/art checks use `mutagen`. The script will try the local
`.codex_tools\python` helper folder used by this sandbox before reporting that
tag checks were skipped.

## Outputs

With `--write-reports`, the script writes these files to the audited folder
unless `--output-dir` is provided:

- `audit_music_batch_report.json`
- `audit_music_batch_report.md`
- `audit_music_batch_report.txt`

In default interactive mode, it also writes:

- `audit_music_batch_approval_plan.json`

The approval plan records approved/rejected proposal codes. It is intentionally
not an apply script.

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
- missing lyrics/karaoke sidecars for non-instrumental tracks
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
merge tracks, delete backups, or modify metadata. It is the audit/proposal layer
that should run before a human or a separate apply tool makes changes.
