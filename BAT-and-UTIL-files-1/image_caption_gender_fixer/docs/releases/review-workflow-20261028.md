# ICGF review workflow update — 2026-10-28

Installed at `C:\BAT\image_caption_gender_fixer` (0.3.0 review update).

## Behavior

- Built-in `his wife` → `her wife`, including case transfer. A priority-200 literal identity rule protects “real man” and preserves every original case exactly, preventing inner “man” replacement.
- Add substitution in the artwork window or console [a]: source, replacement, numeric priority, ordered rule preview and Up/Down/PgUp/PgDn movement. Reordering assigns descending priorities in steps of ten. New rule and order persist in one append to the folder/profile rules sidecar; the proposal is rebuilt before approval.
- The yellow proposed-caption pane is prefilled and editable. Regenerate maps edits back to detected text geometry and creates a fresh proposal. Editing disables Approve; manual wording is retained when another rule is added. Inserted/deleted lines are reflowed within the original caption footprint.
- Artwork Approve and Reject/Skip act on the active review without returning to the console. A token prevents stale or double actions. Approve is unavailable while a render is incomplete, blocked or edited. Warnings appear in the window. Console [y] approves, [a] adds a rule, [e] opens the prefilled editor; ENTER skips.
- Portrait layouts put detected/proposed captions beside the full-height image body; landscape layouts keep two panes beneath the image. Aspect ratio is preserved. Wide terminals align detected/proposed caption lines in two columns. Detected/source text is green; proposed text and ⚠️ warnings are bright yellow; menu choices are colored and show ENTER defaults.
- Automatic floating previews use native SW_SHOWNOACTIVATE for the Tk client and wrapper. They bypass Tk deiconify, which explicitly activates the window even with NOACTIVATE set. Deliberate user clicks permit focus for editing. Persistent worker ownership and joined shutdown remain.
- Terminal detail crops use one fifth of full-preview dimensions. Full images still use the live sibling PAFPlayer Twin DRCS preferences, with attributed internal fallback copies.
- Startup reports package selection/imports, native tools, discovery counts, source hashing, recovery, OCR and rendering in a bounded self-erasing line. JSON and redirected output remain plain. The shared rainbow progress bar now caps its actual formatter width, including very fast refreshes and terminal shrinking.
- Normal OCR compares bounded grayscale/upscaled and caption-panel candidates with mapped source coordinates and quality scoring. It retains confident recognized words and removes isolated low-confidence fragments without inventing text. Eco mode uses fewer passes. Cache algorithm 2 requires one fresh pass for old entries; completed algorithm-2 results resume/reuse normally. Existing .ocr bytes remain retained.
- New corrected outputs use `-genderfixed`. Encountered legacy suffixes receive non-overwriting verified renames with collision numbering, append-only history aliases and recoverable rename intent. Undo still locates preserved originals and handles changed corrected content. Dry runs report planned names without mutation.

## Validation

- **241 installed tests passed**, 94.998 seconds; unraisable Tk warnings treated as errors. Includes the complete relocation, original-preservation, OCR/cache, review, approval-integrity, rollback/undo/recovery and offline package tests.
- Real Tk controls tested for priority/reorder saving, prefilled caption edits, disabled/blocked approval, single-action delivery, portrait height, passive focus and joined worker lifecycle. Source hashes remain unchanged when skipping. Edited captions rebuild with a different transaction before committing.
- Generated photographic-noise/black-panel OCR fixture retained at least 90% of expected words with valid mapped geometry and bounded processing time; alternate candidates must preserve confident existing words. OCR remains fallible and final wording/rendering requires review.
- The installed icgf.bat ran in a real ConPTY: three generated PNGs were prefetched, then all three reused with --verbose. Cache bytes and source hashes stayed unchanged, no history/proposal was created, both exits were 0, and startup stages were visible. Doctor verified all **2,022 dependency files**. No dependency or shared utility was changed/downloaded.
- The terminal smoke run preserved production state exactly across its own before/after snapshot. A separate interactive run updated one already-existing session during development; its newer state was left intact. Other pre-deployment state files retained their hashes. Validation used generated fixtures and did not process real user images.
- Initial installed checks exposed Tk map-time activation and one fast-refresh width overflow. The final native show and width cap passed the complete installed run. Root files remain only the launcher and README. Restart an older running process to load the updated modules.

## Files

- `review-workflow-20261028-acceptance.json`
- `review-workflow-20261028-tests.xml`

## Complete C:\BAT operation disclosure

Every agent replacement had a verified sibling backup first. Root backups were then moved to runtime/backups/implementation. No backup or source was permanently deleted. The separate concurrent-run audit file is identified below as observed activity.

| Action | Full path | Note |
| --- | --- | --- |
| Modified | `C:\BAT\image_caption_gender_fixer\docs\implementation-status.md` |  |
| Created | `C:\BAT\image_caption_gender_fixer\docs\implementation-status.md.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\docs\pafplayer-preview.md` |  |
| Created | `C:\BAT\image_caption_gender_fixer\docs\pafplayer-preview.md.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\review-workflow-20261028-acceptance.json` | Release evidence |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\review-workflow-20261028-tests.xml` | Release evidence |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\review-workflow-20261028.md` | Release evidence |
| Modified | `C:\BAT\image_caption_gender_fixer\docs\requirements-checklist.md` |  |
| Created | `C:\BAT\image_caption_gender_fixer\docs\requirements-checklist.md.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py` |  |
| Created, Renamed | `C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py.bak.202610281702.replaced-by-chatgpt.bak` | Moved to C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\image_caption_gender_fixer.py.bak.202610281702.replaced-by-chatgpt.bak |
| Modified | `C:\BAT\image_caption_gender_fixer\README.md` |  |
| Created, Renamed | `C:\BAT\image_caption_gender_fixer\README.md.bak.202610281702.replaced-by-chatgpt.bak` | Moved to C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610281702.replaced-by-chatgpt.bak |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\image_caption_gender_fixer.py.bak.202610281702.replaced-by-chatgpt.bak` | Archived replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610281702.replaced-by-chatgpt.bak` | Archived replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\logs\30e41b3c-a5bb-4351-af42-9d0894634452.jsonl` | generated-image smoke log |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\logs\496cbbfb-20c5-455b-b629-5bb249b9fdf3.jsonl` | separate concurrent interactive run (observed only) |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\logs\9ff12929-bd74-494c-8f7e-d2f1e3c897fa.jsonl` | generated-image smoke log |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\caption_editor.py` |  |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610281714.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\history.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\history.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\name_migration.py` |  |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\ocr_cache.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\ocr_cache.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\ocr_quality.py` |  |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py.bak.202610281707.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py.bak.202610281714.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\presentation.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\rule_editor.py` |  |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\rules.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\rules.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\sessions.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\sessions.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\transactions.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\transactions.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created, Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_artwork_controls.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_artwork_controls.py.bak.202610281707.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_completion.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_completion.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_images.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_images.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_ocr_prefetch.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_ocr_prefetch.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_ocr_quality.py` |  |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_paf_album_art.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_paf_album_art.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_recovery.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_recovery.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_review_and_platform.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_review_and_platform.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_review_workflow.py` |  |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_transactions.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_transactions.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_transparent_ocr.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_transparent_ocr.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |
| Created | `C:\BAT\image_caption_gender_fixer\tests\unit\test_review_rules.py` |  |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\unit\test_rules.py` |  |
| Created | `C:\BAT\image_caption_gender_fixer\tests\unit\test_rules.py.bak.202610281702.replaced-by-chatgpt.bak` | Verified replacement backup |

Observed separate interactive state update (left intact):
- Modified externally: `C:\bat\image_caption_gender_fixer\runtime\state\sessions\d947422b-7e6e-45ba-9b1d-ae69544374c8.json`.
