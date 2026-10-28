# Image Caption Gender Fixer

Local Windows OCR and reviewed caption correction. Originals are preserved,
undo restores their exact bytes, and processed-image history travels with each
image folder in hidden, unencrypted `.history.icgf`.

The installation is **`C:\BAT\image_caption_gender_fixer`**. Its only root files
are `image_caption_gender_fixer.py` and `README.md`; dependencies, source, state,
tests, and documentation live in subdirectories. Move the entire directory
together. The caller's working directory remains the default image target.

Startup uses a single self-erasing status line for package selection/imports,
discovery counts, source hashing, recovery checks, OCR preparation and rendering.
JSON and redirected output remain free of terminal animation and ANSI colors.

## Requirements and first run

Use **Windows CPython 3.10 x64 with Tcl/Tk**. Python itself is a prerequisite;
required Python packages, their DLLs, Tesseract, English fast OCR data,
ImageMagick, and 7-Zip are included. No pip command, environment activation, or global package
change is needed. The launcher re-enters isolated mode before application imports.
Unsupported interpreter ABIs are rejected clearly; help/version still work.

The `icgf` / `image-caption-gender-fixer.bat` aliases explicitly run console
Python through Windows `py -3.10`, wait until the complete job finishes, and
return its exit status. An unregistered interpreter can be selected through
the `ICGF_PYTHON` environment variable (the full path to `python.exe`). Direct
launcher use also waits for its isolated child. No `.py` file association or
detached `execv` restart is used.

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
Explicit directory junctions such as `C:\new` → `T:\new` resolve to physical
paths before discovery and journaling. Linked image files and unknown reparse
providers are refused; recursive scans skip junction children to avoid cycles.
Installation aliases remain excluded. Hard links require review. Network targets require
`--allow-network`; that flag does not authorize downloads or promise reliable
remote locking, atomicity, durability, or recycling. Unsafe operations stop.

## Prepare OCR ahead of time

Run `icgf --ocr`, `icgf --ocr-only`, or `icgf -o` in the image folder. All three
options do the same thing. Targets and `--recursive` work as usual, for example:

```text
icgf --ocr-only "*.jpg"
icgf -o . --recursive
```

Normal-quality OCR now compares a bounded number of grayscale/upscaled scans
and caption-panel scans, maps words back to source coordinates, and retains
confident existing words when considering alternate results. It suppresses
isolated low-confidence photo fragments without inventing or correcting wording.
`--eco` uses fewer passes. The stronger OCR policy has a new cache key: older
results are retained in `.ocr`, but need one fresh pass before reuse under this
policy. Afterward `-o` continues to reuse completed results across interruptions.

OCR-only saves recognized text and word positions in a **hidden `.ocr` file in
each image folder**. It opens no review window, creates no correction job or
proposal, changes no original image, and writes no processed-image history.
Existing unfinished jobs are left alone and their menu is bypassed. JSON output
includes the full caption and cache path. Normal terminal output uses one compact
shared rainbow progress bar with completed/total counts, percentage, ETA and a
shortened current filename. Counts stay beside a bounded-width bar rather than
at the far edge of a wide terminal. A short completion summary reports newly
saved, reused, deferred and failed images; successful images do not flood the
scrollback with OCR fragments or a second JSON dump.

Use `icgf -o --verbose` to show every complete caption in labeled, wrapped blocks
above the bar. Warnings and errors also print above it. Narrow windows use a
shorter layout, and resizing does not pad to the old terminal width. Terminal
control characters in displayed OCR are escaped; saved text is preserved. Use
`--json` or redirect stdout for complete structured results, including captions.
An already running batch keeps its original layout until the next launch;
completed OCR remains cached when you interrupt and rerun `-o`.

Later, ordinary `icgf` automatically reuses matching saved initial OCR. Cache
entries match image bytes, OCR engine, English model and quality settings, so
renaming an image or folder preserves reuse; changed images or `--eco` settings
get fresh OCR. Rules and profiles are applied afresh. Rendering and verification
of proposed corrections still run normally. Ordinary processing and dry runs
read `.ocr` but do not create or update it; only OCR-only fills the cache.

The cache is local, unencrypted text with word geometry. Updates append checked
records without replacing older entries; a hidden `.icgf.lock` serializes folder
writes. Interrupted batches retain completed records: rerunning OCR-only skips
them. Invalid/incomplete records are ignored with a warning; their bytes and all
valid completed entries are retained, and new results append safely. An unrelated
or unrecognized `.ocr` file is never replaced: normal processing recognizes again,
while OCR-only reports that it could not save.
Do not combine OCR-only with `--resume` or `--dry-run`.

## Rules, profiles, and exclusions

The built-ins run in descending numeric priority:

| Priority | Rule |
| ---: | --- |
| 200 | `real man` → itself; protects the phrase, preserving exact case |
| 100 | `boi` → `boy` |
| 10 | `good boy` → `good girl` |
| 10 | `boy` → `girl` |
| 10 | `man` → `woman` |
| 10 | `husband` → `wife` |
| 10 | `his wife` → `her wife` |

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
Review uses **both PAFPlayer terminal artwork and its floating-artwork rendering
routines**. The tool first looks beside itself in `..\PAFPlayer\PAFPlayer.py` and
loads only the relevant installed artwork definitions, without importing/starting
the player. Its own explicitly attributed copies remain the fallback when that
source is absent/incompatible. `doctor` reports the actual source/version/hash.

The terminal shows the original, crops, masks, repair-only views, and complete
proposal through PAFPlayer's **Twin DRCS** artwork pipeline. It reads PAFPlayer's
current detail/seam preferences without changing them. The current saved profile
is 2x Twin DRCS (granularity 3), detail mode 9 with 2x4 subcells for both artwork
selectors, and seam strategy 5. This path uses no Chafa or SIXEL encoder.
A persistent floating window follows the **last image rendered**; it ends on the
complete proposal while the console awaits your review decision. Resizing keeps
the full aspect ratio. Transparency uses a checkerboard in the window. Complete
detected/proposed captions, including unchanged lines, appear in both the console
and selectable, scrollable caption panes. Portrait previews place detected text on
the left and proposed text on the right, giving the image the body’s full height.
Wide terminals also compare captions side by side. Detected text is green and
proposed text is bright yellow; warnings begin with ⚠️ in bright yellow.
Detail crops use one fifth of the full terminal preview dimensions. No-match images also report their full
detected caption. OCR can be wrong; verify it against the image.

The floating window provides **Approve**, **Reject / Skip**, **Add substitution**,
and **Regenerate from edits**. The yellow proposed-caption pane is already filled
in: edit it directly, then regenerate. Typing disables approval until the edited
proposal has been rendered and reviewed. Line insertions/deletions are reflowed
within the detected caption footprint; excessive wording can still require a
visual adjustment. Window controls and console choices act on the same proposal.
Automatic display and updates leave keyboard focus in the console; a deliberate
click permits interaction with the window. Warnings also appear in the window.

The console uses **[y] approve**, **[a] add rule**, **[e] edit caption**, and
**ENTER=skip**, with the other review actions retained. Add substitution asks for
source, replacement and numeric priority. Preview the ordered rule list, select
any rule and use Up/Down or PgUp/PgDn to move it. Higher entries have higher
numeric priority; reordering assigns descending priorities in steps of ten.
The console rule editor supports the same keys. One folder-rule append saves
the new substitution and ordering; the current image is then regenerated.
Adding a rule preserves prior manual caption edits. Intentional identity rules
reserve their matching original spans across lower priorities, preventing an
inner rule from changing “real man.” Hiding/closing the floating window does not approve or cancel an
image; the next preview can reveal it again. The window is owned by one GUI thread
and cleanly joined at program shutdown, before the shell returns. `--no-preview`
retains console questions and full captions. Redirected/JSON output opens no image
window and contains no ANSI or animated progress. Interactive progress uses the shared
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
- Corrected: `image-genderfixed.jpg`. Encountered legacy `-gendeerfixed` output names
  are corrected without overwriting collisions. Durable rename journals and
  append-only history aliases preserve undo; image bytes remain unchanged.
  Dry runs only report the planned rename.
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
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py undo 'image-genderfixed.jpg'
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
The interactive menu shows numbered jobs with folder, update time and progress.
Choose a number rather than copying an internal ID. `?` explains the choices;
invalid input is retried. Trash-and-forget offers one job or `a` for all jobs,
then asks for confirmation; originals are retained. A single job needs no second
selection prompt. OCR-only bypasses this menu entirely.
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

`doctor` checks the two-file root, required imports/tools, the PAFPlayer-copy
renderer and Tcl/Tk availability, selected bundle hashes,
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
- [PAFPlayer-copy attribution and review-window behavior](docs/pafplayer-preview.md)
- [Full specification](docs/implementation-specification.txt) (the 0.3.0 preview/junction/launcher changes supersede its older Chafa/reparse wording)
- `docs/releases`: exact validation results and every affected `C:\BAT` path.
