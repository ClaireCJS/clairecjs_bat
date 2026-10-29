# ICGF artwork, OCR and fitting update — 2026-10-29

The installed artwork window reopens on its next image update after close/hide,
keeps automatic updates passive after prior interaction, and restores the full
original after detail crops when a proposal is blocked. Portrait review captions
stay beside the image at usable window widths. Changed caption characters pulse
between bold and regular every 650 ms without disappearing.

Artwork controls include Approve, Reject/Skip, Ignore substitution, Add
substitution/priority, Regenerate from caption edits, Move/squeeze, Rename image,
Delete/Recycle, Defer, Cancel and Hide. Ignore offers a folder exception or a
one-time exception; Skip only leaves this image unchanged. Rename starts with the
source filename filled in, preserves collisions and image bytes, journals the
move for interrupted-job recovery, and regenerates before approval. Recycle acts
only on the current source after a separate confirmation, uses the operating
system Recycle Bin and has no permanent-delete fallback.

Explicit image targets bypass unrelated unfinished-job selection. Bare `icgf`
retains its numbered jobs menu, with `[h]elp`, `help` and `?`. An explicit
`--resume` still selects its requested job. The newer existing force-OCR,
normal-run cache, single-key adjustment menu and built-in rule changes were
preserved. Two outdated rule test expectations were aligned with those existing
built-ins; this release did not overwrite their rule implementation.

Fitting first uses ordinary font/spacing trials, then safe right/left placement,
then neighboring-word compression. Movement is restricted to the source caption
panel/column and a maximum local shift of 32 pixels. Horizontal and font-size
adjustments may be combined within a 20% reduction each. Repair masks are clipped
to the caption lane. An edit remains blocked if it cannot fit safely; alternatives
still require approval. Full-caption spans and the original image stay intact.

OCR adds bounded weak-block/line retries, padded enlargement, contrast correction,
bright/dark ink extraction and threshold alternatives. Strong source words guard
selection of replacement OCR candidates; short snippets use a stricter retention
threshold to preserve intentional words such as boi. A TSV parser correction prevents leading
quotes in recognized words from swallowing later records. Cache algorithm 3
appends improved results under a new key and preserves old hidden `.ocr` data.
No package or language-model download was required; eco mode retains its lighter
path. Preprocessing follows the official
[Tesseract quality guidance](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html).

## Validation

**357 installed tests passed**, zero failures/errors/skips. This includes
real Tesseract OCR, image correction/undo, interruption recovery, Windows Recycle
Bin behavior on isolated test images, GUI controls, passive updates, close/reopen,
caption layout/pulsing, explicit targets, private dependencies and relocation.

JUnit evidence: `C:\codex\clairevironment\release-output\image-caption-gender-fixer\focus-targets-20261028\installed-results-7dbfa9b21ee74144a9873faa8afbfee5.xml`.

| Fixture | Previous word errors | Current word errors | Previous seconds | Current seconds |
| --- | ---: | ---: | ---: | ---: |
| clean | 0 | 0 | 0.469 | 0.828 |
| small-photo | 9 | 1 | 0.859 | 1.594 |
| faint-jpeg | 1 | 1 | 0.734 | 0.719 |
| outlined-photo | 5 | 0 | 0.86 | 1.328 |

The four neutral synthetic fixtures contain 60 reference words in total. Word
edit errors decreased from 15 to 2; the small/outlined photo cases account for
the improvement. These fixtures measure regression coverage and are not an
accuracy guarantee for arbitrary user images. One faint-image spelling error
and one very-small-text spelling error remained. Measured timings vary by load.
The benchmark images and exact OCR strings remain in the workspace evidence.

Windows activation protection uses a GUI-thread-scoped hook released at shutdown,
plus NOACTIVATE during automatic updates; physical mouse activation is permitted.
See [CBTProc](https://learn.microsoft.com/en-us/windows/win32/winmsg/cbtproc),
[SetWindowsHookExW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowshookexw)
and [CBTACTIVATESTRUCT](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-cbtactivatestruct).

Root files remain exactly `image_caption_gender_fixer.py` and `README.md`.
Verified sibling replacement backups were made before deployment; README backups
were then moved into `runtime/backups/implementation` to keep the root minimal.
No file was permanently deleted. Restart an already running ICGF after finishing
the current image to load the new modules.

## C:\BAT changes performed by this operation

- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610290107.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py.bak.202610290107.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py.bak.202610290107.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py.bak.202610290107.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\adjustment_menu.py.bak.202610290107.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610290107.replaced-by-chatgpt.bak`
- Renamed: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610290107.replaced-by-chatgpt.bak` → `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610290107.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610290107.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\tests\unit\test_requested_rules_columns.py.bak.202610290107.replaced-by-chatgpt.bak`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\adjustment_menu.py`
- Modified: `C:\BAT\image_caption_gender_fixer\README.md`
- Modified: `C:\BAT\image_caption_gender_fixer\tests\unit\test_requested_rules_columns.py`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_artwork_reopen.py`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_popup_updates.py`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_explicit_targets.py`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_move_squeeze.py`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_review_refinements.py`
- Created: `C:\BAT\image_caption_gender_fixer\tests\unit\test_job_help_targets.py`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610290114.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py.bak.202610290114.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py.bak.202610290114.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\adjustment_menu.py.bak.202610290114.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610290114.replaced-by-chatgpt.bak`
- Renamed: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610290114.replaced-by-chatgpt.bak` → `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610290114.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610290114.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_popup_updates.py.bak.202610290114.replaced-by-chatgpt.bak`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\adjustment_menu.py`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\file_actions.py`
- Modified: `C:\BAT\image_caption_gender_fixer\README.md`
- Modified: `C:\BAT\image_caption_gender_fixer\tests\integration\test_popup_updates.py`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_artwork_file_actions.py`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\ocr_quality.py.bak.202610290128.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\ocr_cache.py.bak.202610290128.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py.bak.202610290128.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610290128.replaced-by-chatgpt.bak`
- Renamed: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610290128.replaced-by-chatgpt.bak` → `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610290128.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610290128.replaced-by-chatgpt.bak`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\ocr_quality.py`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\ocr_cache.py`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py`
- Modified: `C:\BAT\image_caption_gender_fixer\README.md`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_ocr_retry_accuracy.py`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_caption_fit_lane.py`
- Created: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\ocr_quality.py.bak.202610290134.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_popup_updates.py.bak.202610290134.replaced-by-chatgpt.bak`
- Created: `C:\BAT\image_caption_gender_fixer\tests\integration\test_ocr_retry_accuracy.py.bak.202610290134.replaced-by-chatgpt.bak`
- Modified: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\ocr_quality.py`
- Modified: `C:\BAT\image_caption_gender_fixer\tests\integration\test_popup_updates.py`
- Modified: `C:\BAT\image_caption_gender_fixer\tests\integration\test_ocr_retry_accuracy.py`
- Created: `C:\BAT\image_caption_gender_fixer\docs\releases\artwork-ocr-fitting-20261029.md`
