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
icgf -of .
```

Use **`-of`** (also `--ocr-force`) to force OCR-only across all matching images,
including previously processed/corrected files, preserved image backups and undo
archives. It recognizes them again even when matching OCR is already cached,
then appends refreshed results to `.ocr`; older records remain preserved and
later ordinary runs reuse the newest result. It opens no review window or jobs
menu and does not edit/rename images or change processed-image history.
Internal preview/mask files and state files remain excluded. Existing recursion,
hidden/system-file and network options still apply. Like `-o`, it cannot be
combined with `--resume` or `--dry-run`.

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
of proposed corrections still run normally. Ordinary processing also saves newly
recognized initial OCR to hidden `.ocr` files, before review, including images
you skip or cancel and images with no substitutions. A later normal run or `-o`
reuses those results. Dry runs and read-only analysis never create or update
the cache. A cache write failure warns and allows ordinary review to continue;
OCR-only still reports failure if it cannot save its requested results.

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

Review choices include approve, skip, defer, cancel, **fix OCR**,
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
per run; cancellation preserves pending work.

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


## Single-key review and visual adjustments

Review, region selection, visual adjustment and background-repair menus act on
one displayed key without ENTER. H explains the current menu; ESC goes back
(or cancels at image review). ENTER uses the displayed contextual default.
For a blocked text fit, ENTER opens visual adjustment, then tries text 5% smaller;
at minimum size it opens the prefilled wording editor instead. A valid proposal
defaults to Skip at review and Back within visual adjustment.

W edits the existing replacement wording without retyping the caption. Numeric,
color and font values have separate prefilled fields. A successful adjustment
regenerates the proposal and still requires image approval.

Background repair is checked independently from replacement text placement.
Gray choices give the actual failure reason, such as no safe neighboring donor
patch; a text-fit failure does not make a working background repair unavailable.
ENTER selects the available background with the lowest boundary/artifact score;
this is a visual heuristic, so inspect the preview before approving the image.


## Artwork review and fitting — 2026-10-29

Close (X), Escape, and Hide only hide the artwork window. The next image update
shows it again without activating it. A cleanly stopped preview worker restarts
on the next update and discards stale review decisions. Automatic initialization,
caption updates, redraws and image changes have a thread-local native activation
guard, including after the user has clicked in the window. Intentional clicks
can still activate its controls. Restart a running ICGF process to load this fix.

Portrait images use the full available image-panel height with detected/proposed
captions beside them (including narrower windows at least 680 pixels wide).
Blocked previews return to the full original after showing detail crops. Changed
caption characters pulse their background in both panes every 650 ms;
they stay visible and retain the green/yellow colors. Caption edits remain filled
in, and Regenerate builds a fresh proposal before approval.

When ordinary fitting fails, ICGF automatically tries safe rightward placement,
then leftward placement, then redrawing one or two nearby unchanged words on each
side with at most 20% horizontal compression. Whole edited lines can be squeezed
within their existing footprint. It never moves across neighboring text, absorbs
another edit, changes the original caption spans or approves an alternative for
you. Fitting diagnostics explain any movement/compression. If still blocked,
**[m]ove/squeeze text to fit** is the default console action. The artwork button
retries all current changes without a console region-number question.

The artwork **Ignore substitution** button lets you select a change and either
remember a phrase exception in the folder or ignore it once. **Reject / Skip**
only leaves the current image unchanged. **Defer** and **Cancel job** are also
available in the artwork window. The existing rule/priority and caption editors
remain available there.

Explicit targets (`icgf .`, `icgf "*.*"`, a filename, or `--literal-path PATH`)
start directly on those images and retain unrelated unfinished queues. No-match
targets also bypass those queues. An explicit `--resume` still resumes the chosen
job. Run bare `icgf` to manage old jobs; the numbered menus offer **[h]elp**
(`help` and `?` work too).


The artwork window also provides **Rename image** and **Delete / Recycle**.
These act on the current source image, never the temporary proposal or crop.
Rename prefills its existing name, keeps the image extension, preserves filename
collisions with ` (1)`, ` (2)`, etc., updates the resumable queue, and rebuilds the
proposal for review. File-action bookkeeping is journaled before the move so an
interruption can be reconciled on resume. Recycle displays the full source path
and requires a separate confirmation (default No), discards the pending correction,
and uses only the Windows Recycle Bin; failure retains the file. No image is
recycled automatically during ordinary caption correction.


## OCR quality and caption-column fitting — 2026-10-29

Normal OCR now adds targeted retries for weak photo-overlay text, not just solid
caption panels: nearby lines are grouped, enlarged, padded, contrast-normalized,
and tested with bright-ink, dark-ink, Otsu and adaptive threshold alternatives.
Single-line and text-block segmentation are chosen from the detected layout.
Extra retry calls are limited to eight per image and clean captions bypass them.
Strong recognized words are retained when choosing alternatives. Eco mode keeps
its lighter scan path. OCR uses actual engine results and does not invent prose.
Literal quotation marks in Tesseract TSV are now read as text; a leading quote
can no longer consume subsequent word records as if they were quoted CSV fields.

The OCR cache algorithm is now version 3. Old hidden `.ocr` records stay intact;
the first scan with this policy appends improved results, and subsequent runs
reuse them. No extra model, Python package, or global installation was added.
On four neutral synthetic caption fixtures, word errors dropped from 15 to 2;
the outlined-photo case improved from 5 errors to zero. These are fixture results,
not a guarantee for every photograph. The two difficult photo examples took about
1.3–1.6 seconds each in the measured run, compared with about 0.9 seconds before.

Rendered replacements stay within their source caption panel/column. Automatic
left/right movement is limited to a small local shift (at most 32 pixels), and
text that still does not fit is compressed with nearby words within its footprint.
Modest font-size and horizontal adjustments can be combined; an edit remains
blocked if no safe fit exists. The repair mask is also clipped to the caption
lane, so fitting cannot erase the adjacent photograph. This restriction concerns
text inside the image; portrait review panes remain beside the displayed image.

## Console menus and artwork controls — 2026-10-29

Console menus adapt to one through four columns, with shared unavailable-action
reasons printed once below the choices. ENTER uses the highlighted default.
Every review choice is available in the artwork window, including
OCR correction, visual adjustment, background comparison,
ignore scopes, help and cancel. Submenus and prefilled value fields also appear
in the window, so these adjustments can be completed there. Editing a caption
keeps adjustment actions disabled until Regenerate applies the draft, preventing
an unrelated adjustment from silently discarding it.

While the console is waiting for a menu choice or text value, **Ctrl+A** restores
the latest artwork window without changing focus. **Ctrl+Alt+A** explicitly
restores it and requests that Windows bring it to the foreground. Closing or
hiding the window retains the pending review; the shortcuts also recover a
stopped preview worker. These are console-local shortcuts, not system hotkeys.
Automatic image updates continue to avoid activating the window.

Artwork startup is independent of terminal preview rendering: a terminal-render
failure or redirected console output no longer prevents the artwork preview.
Preview errors include their diagnostic message and keep console review usable.
Double-click the displayed artwork to open that exact image, proposal or detail
crop with the Windows default image viewer.

Restart a running ICGF process to load these changes. This release does not
change the OCR engine, trained data or OCR cache policy.


## Image-first adaptive layout and artwork keys — 2026-10-29

The review window compares the displayed image size for bottom and side layouts,
using the current window, image shape and button sizes. When side controls leave
a larger image, both caption panes and the review buttons move into the gutters,
leaving the image the full available height. This applies to square images too.
Button columns adapt to the available side width. Wide images keep controls below
when that gives the image more space. Resizing and switching images recompute
the layout without discarding caption edits or the current review.

The displayed letter keys activate their artwork buttons, including I for Ignore,
A for Approve, N for New substitution and G for Regenerate. Keys typed inside a
caption, value field or separate dialog remain text input. Active adjustment
submenus use their own displayed keys. F2 renames the image, Delete opens
the Recycle confirmation, and Escape hides the window. Disabled actions stay disabled.

Changed text now pulses its background only, retaining the same font, foreground
color, line breaks and character positions in both phases. Approve-and-pause and
Skip-and-pause actions have been removed from the console and artwork window.
Use Cancel or interrupt the console to leave the remaining queue for later.


## Multiple artwork windows and Windows shell — 2026-10-29

Each running ICGF process owns a separate artwork window, taskbar identity and
notification-area (tray) icon. Tray tooltips identify the process and current
image. Closing/ hiding artwork retains its tray icon; clicking that icon restores
its window. Right-click offers Show this artwork, Show all ICGF artwork and Hide.
Windows controls whether a notification icon appears on the visible tray row or
in its overflow. ICGF restores its icons if Windows Explorer restarts.

Ctrl+A in an ICGF console restores its own artwork without activation.
Ctrl+Alt+A in any ICGF console, or its artwork window, restores and raises all
active ICGF artwork windows on the same desktop. Each instance must be restarted
after this update to participate. No system-wide hotkey registration is needed.
Automatic image changes remain passive. Native window messages reveal artwork
only; they cannot approve a proposal or perform an image file action.

Artwork review keys are A = Approve, G = Regenerate, R = Reject changes,
I = Ignore and N = New substitution. Console review retains its displayed keys.
Delete opens a confirmation for recycling the current SOURCE image; declining
keeps it. F2 opens Rename with the current source filename prefilled and editable.
Typing and Delete inside a caption or filename field remain normal editing.
