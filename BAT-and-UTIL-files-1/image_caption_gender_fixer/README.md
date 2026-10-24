# Image Caption Gender Fixer

Local Windows OCR and reviewed caption correction. Originals are preserved,
undo restores their exact bytes, and processed-image history travels with each
image folder in hidden, unencrypted `.history.icgf`.

The installation is **`C:\BAT\image_caption_gender_fixer`**. Its only root files
are `image_caption_gender_fixer.py` and `README.md`; dependencies, source, state,
tests, and documentation live in subdirectories. Move the entire directory
together. The caller's working directory remains the default image target.

## Requirements and first run

Use **Windows CPython 3.10 x64**. Python itself is a prerequisite; required Python
packages, their DLLs, Tesseract, English fast OCR data, Chafa, ImageMagick, and
7-Zip are included. No pip command, environment activation, or global package
change is needed. The launcher re-enters isolated mode before application imports.
Unsupported interpreter ABIs are rejected clearly; help/version still work.

```powershell
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py doctor
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py --help
```

Healthy bundled dependencies require no installation prompt or network access.
If required packages are missing or damaged, processing offers an automatic,
verified rebuild from the offline repair archive. The prompt identifies the
dependencies, source, versions, destination, and sizes; declining stops correction.
An interactive restart selects the repaired environment and preserves terminal
review. Missing OCR offers the pinned trusted download after separate consent.
`--yes` never supplies installation consent. JSON/noninteractive runs request an
explicit decision rather than installing software.

## Process images

Run from the image folder, or supply targets:

```powershell
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py 'image.jpg'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py '*'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py '*.png' --recursive
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py '*.png' --dry-run --json
```

Quote wildcards in PowerShell; the program expands them and deduplicates targets.
Recursion requires `--recursive`; hidden/system images require their respective
`--include-hidden`/`--include-system` options. Use `--literal-path PATH` for an
exact unusual filename, or `--` to end option parsing. Use `process` or a full
path when a filename could be confused with an administrative command.

The tool refuses images inside its installation, prunes its installation from
parent scans, and excludes its outputs, backups, undo archives, and previews.
Reparse points are refused. Hard links require review. Network targets require
`--allow-network`; that flag does not authorize downloads or promise reliable
remote locking, atomicity, durability, or recycling. Unsafe operations stop.

## Rules, profiles, and exclusions

The built-ins run in descending numeric priority:

| Priority | Rule |
| ---: | --- |
| 100 | `boi` → `boy` |
| 10 | `good boy` → `good girl` |
| 10 | `boy` → `girl` |
| 10 | `man` → `woman` |
| 10 | `husband` → `wife` |

Thus **`good boi` → `good boy` → `good girl`**, with only the final wording
rendered. At a priority, matches use one snapshot; longest normalized match wins,
then literal over regex, folder and user precedence, creation order, and leftmost
position. Generated text can enter lower priorities. Whole-word boundaries,
Unicode case transfer, bounded regex/stages/output, and cycle checks apply.

```powershell
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py rules explain 'good boi'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py rules add king queen --priority 20 --note 'Preferred wording'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py rules profiles
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py rules show --profile project-name
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py rules ignore boy --context king
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py rules ignore boy --occurrence 0:3
```

Folder rules live in UTF-8 `.image-gender-fixer.stt`, separately from history.
`rules show` displays stable IDs for `rules enable ID` / `rules disable ID`.
Those commands also enable/disable exclusions. `--case transfer|exact|ignore`,
`--punctuation exact|whitespace|flex`, `--regex`, `--priority`, `--note`,
`--scope folder|global`, and `--profile NAME` control saved rules.

Exclusions support a phrase, original OCR character span (`--occurrence START:END`),
context (`--context TEXT`), image SHA-256 (`--image-hash HASH`), session
(`--session-id ID`), or whole scope (`--all-future`). Combine selectors to narrow
one exclusion; separate exclusions are alternatives. Phrase exclusions protect
the original span throughout the cascade. `--scope global` applies future
exclusions across folders. Global positive substitutions are opt-in through
`--global-rules` or `preferences set global-rules on`; reset with `off`.

Profiles remain separate. `conservative` always requires review. A resumed job
uses its stored profile unless explicitly overridden. Rules/exclusions are saved
only when explicitly requested; ordinary OCR correction and skipping save none.
Malformed records are reported and quarantined; unrelated files are preserved.

## Review and visual correction

Every proposed image requires one final approval by default, including level 1.
Chafa shows the original, each original crop, numbered mask, repair-only crop,
corrected crop, and complete proposal sequentially. Geometry is recalculated
before each preview, using roughly 70% of terminal height and 95% of width.
`--no-preview` retains review questions. Redirected/JSON output contains no
terminal images, ANSI, or animated progress. Interactive progress uses the shared
Claire rainbow progress bar. `--eco` reduces initial OCR resolution and CPU use.

Confidence levels:

1. Strong flat-background/font/OCR fit with successful checks.
2. Usable but uncertain styling, fit, or verification; review required.
3. Photographic/complex/low-confidence repair, face/edge warnings, or other
   uncertainty; review required.

Only explicit `--skip-review-for-confident-ones` may bypass a safe level 1
proposal. The original spelling `--skip-reivew-for-confident-ones` is also accepted.
Neither alias nor `--yes` bypasses levels 2/3 or a blocked proposal.

Review choices include approve/pause, skip/pause, defer, cancel, **fix OCR**,
visual adjustment, background comparison, and ignore. OCR correction happens
after the first proposal; it changes detected text, grouping/reading order,
bounds, or rotation, then reruns the rules and rendering. It never silently
becomes a learned substitution. Mask ownership/effects are adjusted separately.
No-match images skip quietly unless `--review-no-match-images` is requested.

Visual controls include smaller/larger, `move dx,dy`, `tracking N`, `font PATH`,
`color #RRGGBB[AA]`, `opacity 0..1`, `outline N`, `outline-color`,
`shadow dx,dy,blur`, `shadow-color`, `rotation N`, `mask +/-N`,
`extend left|right|up|down N`, `include|exclude outline|shadow`, `protect BOX`,
`box x1,y1,x2,y2`, `wording TEXT`, `skip`, and `reset`.

Background comparison offers fill, gradient, Telea/Navier inpainting, and safe
neighboring patches. A solid `label #RRGGBB[AA]` treatment requires an explicit
choice. Glyph masks preserve surrounding pixels; replacements are measured with
their outline/shadow/rotation and checked against image bounds and protected
neighboring text. If no safe fit exists, the original and blocking reason are
shown with adjustment/OCR/skip/cancel choices; approval is unavailable.

Font choices are ranked approximations, including weight/italic candidates.
Face detection and strong-edge/seam warnings are conservative local heuristics.
Photographic reconstruction cannot recover unknowable original detail reliably;
inspect candidates and defer an unacceptable edit. No neural model or font is
downloaded automatically. Any change to a proposal requires approval again.

## Outputs, history, and undo

Renders, masks, comparison crops, and staging images are hidden `.icgf-UUID-*`
files **beside the source**. Exact ownership, identity, and hashes govern cleanup.
Changed or ambiguous artifacts are retained and reported. On approval:

- Original: `image.jpg` → `image.jpg.bak.YYYYMMDDHHMM.replaced-by-chatgpt.bak`.
- Corrected: `image-gendeerfixed.jpg` (intentional suffix spelling).
- Collisions: numbered before the final extension, preserving both files.

Source identity, size/time, and SHA-256 are rechecked under Windows leases;
the approved stage hash is rechecked and protected against writers. Journals
precede renames. Success requires preserved original bytes, verified output,
and a durable committed event in the correct folder's `.history.icgf`.

Keep hidden `.history.icgf` with its image folder. Its relative references and
hashes survive folder moves/renames and file renaming recognition. Exact local
history is authoritative; the central hash cache is derived and may be absent.
Cross-folder recognition covers histories already observed, not an arbitrary
disk search. Perceptual similarity never automatically proves prior processing.
Checksums detect accidental corruption, not deliberate tampering with rewritten
checksums. There is no encryption or machine-bound key.

```powershell
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py history status .
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py history verify .
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py undo 'image-gendeerfixed.jpg'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py undo '*' --keep-undo-archives
```

Undo archives corrected work before restoring the original byte-for-byte.
Choose keep/recycle this archive, the rest of the run, or always; preferences
are visible/resettable through `preferences show`, `set undo-corrected
ask|keep|recycle`, and `reset undo-corrected`. A changed corrected file is kept
unless explicitly approved for recycling, even under an always-recycle preference.
Recycling failures retain data; there is no permanent-delete fallback.

## Pause, resume, and recovery

Ordinary processing offers unfinished jobs before creating a new job. Inspect,
resume, forget, retain-and-start-new, or cancel; `--yes` selects none of these.
JSON mode reports the required choice and job IDs. Cancellation preserves the
current source and a resumable job. Deferred work is revisited at most once
per run; approval-and-pause preserves pending work.

```powershell
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py sessions list
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py --resume
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py --resume SESSION-ID
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py --new-session '*.png'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py sessions abandon SESSION-ID
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py recover --dry-run --json
```

Forgetting recycles only the job and verified owned artifacts; completed images,
original backups, history, rules, and preferences remain. Interrupted filesystem
transactions must be recovered first. A moved live-job target is reported rather
than guessed; cross-computer job/undo portability is not promised.

Mutating commands recover deterministic interrupted transactions or stop with
recoverable evidence. Help, version, dry runs, and read-only inspections perform
no startup recovery or cleanup. `history backup` can copy even a corrupt tail
without changing it. See [recovery design](docs/recovery.md) before handling an
ambiguous state. `--recover-from-backups` is explicit, confirmed fallback recovery.

## Formats, privacy, and maintenance

PNG/JPEG are supported. Animated/multiframe and unvalidated formats are explicitly
deferred. Orientation is baked once with updated tags; dimensions, alpha, ICC,
DPI, and relevant EXIF are preserved deliberately. Lossless pixels outside the
affected region remain identical when no global orientation transform is needed.
JPEG re-encoding changes pixels beyond the edited region; the original backup
always remains byte-identical. New outputs have new creation timestamps; original
backup attributes/timestamps are retained by rename where supported.

All analysis stays local. No images, OCR, paths, hashes, history, or rules are
uploaded. There is no telemetry, crash upload, or automatic update check. Local
operation logs omit OCR/rule content and target paths; crash reports contain
exception types and code locations, not exception text or local variables.
Interactive review/explain deliberately displays relevant content locally.

Recognized redundant setup downloads are recycled after successful installation
or repair and on processing startup. Working packages and the offline repair ZIP
remain. Use `environment cleanup --dry-run --json` or `environment cleanup --json`.
Recycled files still occupy drive space until the Windows Recycle Bin is emptied
separately. No unrelated, changed, linked, or busy download is silently discarded.

`doctor` checks the two-file root, required imports/tools, selected bundle hashes,
pending journals, malformed sessions, and retained artifacts without repairing.
For dependency issues, use the consent-based `environment repair` workflow.
Never remove original image backups or `.history.icgf` to resolve a warning.

To uninstall, first inspect unfinished jobs/recovery state. Recycle the tool
directory through Windows; preserve image folders, original backups, corrected
images, undo archives, and their history. Uninstalling the tool does not undo edits.

## Development and detailed documentation

```powershell
python -B -I -S C:\BAT\image_caption_gender_fixer\tests\run_tests.py -q
```

Tests use generated disposable images outside the installation. Native OCR,
Windows transactions/leases/locking/recycling, image rendering/metadata, exact
undo, package repair/relocation, and interrupted recovery have real tests.
Dependency-download/install orchestration is mocked; tests never access the
internet or install global software.

- [Requirements and acceptance evidence](docs/requirements-checklist.md)
- [Recovery, history, and state design](docs/recovery.md)
- [JSON and exit-code contract](docs/json-and-exit-codes.md)
- [Dependency versions, provenance, licenses, and reproduction](docs/bundled-dependencies.md)
- [Full specification](docs/implementation-specification.txt)
- `docs/releases`: exact validation results and every affected `C:\BAT` path.
