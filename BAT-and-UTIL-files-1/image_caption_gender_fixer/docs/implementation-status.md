# Release 0.3.0

The later 2026-10-28 OCR console update replaces per-image raw caption scrolling
and terminal JSON dumps with compact progress and a human completion summary.
It retains the shared Claire rainbow bar, keeps counters/ETA adjacent to a bounded
bar and adapts to narrow/resized terminals. `-o --verbose` shows complete labeled
caption blocks through tqdm's safe write path; warnings/errors use the same path.
Structured JSON/redirected exports and hidden `.ocr` cache contents are unchanged.
See `releases/ocr-console-20261028.md` for installed console validation.

The 2026-10-28 update adds OCR prefetch and a numbered unfinished-job menu.
`--ocr`, `--ocr-only` and `-o` save initial OCR in hidden folder-local `.ocr`
files. This mode bypasses correction jobs and transaction recovery, writes no
processed history and changes no image. Normal processing and dry runs reuse
valid saved OCR but do not populate the cache. Image/model/engine/quality hashes
prevent stale reuse; folder and image renames preserve matches. Saved text and
word geometry are plaintext append-only records, separate from `.history.icgf`.
Post-render verification remains live. The jobs menu shows folder/time/progress,
uses job numbers, retries invalid input/help, and offers confirmed recycling of
one or all jobs. Existing JSON/explicit --resume ID interfaces remain supported.
See `releases/ocr-jobs-20261028.md` for installed validation and changed files.

The supported Windows CPython 3.10 x64 PNG/JPEG workflow is installed at
`C:\BAT\image_caption_gender_fixer`. Only the launcher and README are root
files. Python must include Tcl/Tk for the image window; required Python packages
and OCR/native tools remain private and already bundled.

The 2026-10-27 release fixes early return to the calling shell: both the initial
isolated launcher and an interactive package-repair restart wait for their worker.
The `icgf` aliases explicitly run console Python instead of a `.py` association,
and return its final exit status. `ICGF_PYTHON` selects an unregistered interpreter.

Explicit directory junctions such as `C:\new` to `T:\new` resolve to physical
targets before queuing. Linked image files and unknown reparse providers remain
refused; recursive scans skip junction children and installation aliases remain
excluded.

Image review now uses both PAFPlayer terminal Twin DRCS and a persistent floating
artwork window following the last image rendered. The tool prefers artwork
definitions loaded from the installed sibling `..\PAFPlayer\PAFPlayer.py`,
without executing player startup, and preserves attributed internal copies as
fallback. Doctor reports origin, version, path, and hash. Full detected/proposed
captions include unchanged lines in the console and window. Console review remains
authoritative; closing the window hides it and never approves an image. Exactly
one GUI thread owns Tk, and program shutdown joins it before the shell returns.
The DRCS pipeline reads current PAFPlayer settings without saving or migrating
them: currently 2x Twin DRCS, detail mode 9 (2x4 subcells) for both selectors, and
seam strategy 5. It uses PAFPlayer's bank definitions, quantization and cell
styling directly; the selected profile calls no Chafa or SIXEL encoder.

Original backups, hidden folder history, undo, sessions, recovery, consent gates,
and safe setup-download recycling retain their protections. Existing user jobs
are preserved. Optional OCR/style controls use the same running console and then
render a fresh proposal; the shell remains blocked until the job finishes.

See `pafplayer-preview.md` for exact copy attribution and behavior,
`requirements-checklist.md` for acceptance mapping, and
`releases/pafplayer-previews-20261027.md` for actual installed tests, limitations,
and every affected C:\BAT path. Earlier release reports remain historical records.

Photographic reconstruction and font matching remain best-effort and reviewed.
Animation/unvalidated formats defer; JPEG is lossy; the interpreter is not bundled.
All test images are generated disposable data; no real user image is edited by
validation. Dependency download/installer control tests remain mocked.


## Review workflow update — 2026-10-28

Portrait previews put the detected/proposed captions beside the full-height image.
The passive artwork window now supports Approve, Reject/Skip, Add substitution
with priority and keyboard ordering, and direct editing of the prefilled proposed
caption followed by regeneration. Approval is invalidated by edits and tied to a
single current proposal. Warnings appear in the window and in bright yellow in
the terminal. Console choices are colored and show ENTER defaults; [y] approves,
[a] adds a rule and [e] opens the prefilled caption editor. Detail terminal crops
are one fifth of full preview dimensions. Startup status messages erase in place.

Built-ins add `his wife` → `her wife` and a case-preserving protective `real man`
identity rule. Ordered priorities persist in a single folder-rule append.
OCR uses bounded higher-resolution/grayscale and caption-panel candidates;
cache algorithm 2 requires a one-time refresh of older OCR results. New outputs
use `-genderfixed`; legacy `-gendeerfixed` names receive verified non-overwriting
renames with recoverable journals and history aliases that preserve undo.
See `releases/review-workflow-20261028.md` for validation and file disclosures.
