# Requested substitutions and newspaper OCR columns — 2026-10-28

This focused operation implements only the rules/column request from the side conversation. It does not certify or complete the separate parent-thread release or its artwork-focus work.

## Rules

| Priority | Source | Replacement |
| ---: | --- | --- |
| 400 | `another man` | a man (protected from later substitutions) |
| 300 | `my hubby` | my wife |
| 300 | `he has no idea` | she has no idea |
| 300 | `not with his cock` | not with her cock |
| 150 | `not with his` | not with her |
| 150 | `tease him` | tease her |
| 150 | `tying her` | tying him |
| 150 | `his little` | her little |
| 150 | `keep him` | keep her |
| 5 | `hubby` | wife |

Existing built-in IDs remain stable. The `real man` identity whitelist preserves its exact original case and reserves its original span, so the inner `man` rule cannot run later. `another man` has a protected replacement and remains `a man`; a separate nearby `man` still follows the normal cascade. Case transfer remains active. The protection flag survives rule-store serialization.

## OCR columns

ICGF copies/adapts the column slicing, width calculation and padded rendering routines from `C:\BAT\print_with_columns.py` (functions at lines 473, 515, 591; source SHA-256 f0cfcec8cec11d921a1f28ec4615f3f53e9a9401ce35d6b5cdf909cad8a37aaf). The copy is explicitly attributed in newspaper_columns.py. The original newspaper commands are unchanged.

Verbose OCR-only captions (`icgf -o --verbose`) flow down columns and then across. Detected/proposed review text uses synchronized column pairs, retaining green source and bright-yellow proposal colors. Column count adapts to the terminal width/height. Narrow terminals wrap safely. ANSI/control text from OCR is escaped; wide and combining characters are measured for alignment. Structured captions, cache records and source-image contents are unchanged. No packages were installed or shared utilities changed.

## Validation

Installed focused suite: **87 passed**, 11.789 seconds. Evidence: `C:\codex\clairevironment\release-output\image-caption-gender-fixer\side-rules-columns-20261028\installed-results-08a59e7c9783457f96a47a3325a248de.xml`.
Checks include all ten substitutions and priority tiers; case transfer; protected replacement/whitelist; rule-store persistence; old cascade/IDs; newspaper reading order; widths 8/40/80/120/240; long lines and combining/wide characters; safe control display; actual verbose OCR integration; original preservation and OCR cache reuse/invalidation/interruption. Tests used generated fixtures, with reports/caches in the workspace or temporary folders. No real user images or unfinished jobs were processed by this operation.

A concurrent CLI update was detected before any file replacement. Only the verbose-caption block was rebased onto that current CLI, preserving its unrelated changes. The installed targeted tests and final file hashes were then verified. Restart ICGF to load the new rules/display code.

## Complete C:\BAT disclosure

Verified sibling backups were created before replacing the three existing source files. No files were deleted or renamed by this operation.

| Action | Full path |
| --- | --- |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\rules.py.bak.202610281726.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\presentation.py.bak.202610281726.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610281726.replaced-by-chatgpt.bak` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\rules.py` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\presentation.py` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\newspaper_columns.py` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\unit\test_requested_rules_columns.py` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_newspaper_columns.py` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\side-rules-columns-20261028.md` |
