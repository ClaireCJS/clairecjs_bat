# Move/squeeze fitting that broadens the initial search — 2026-10-29

Previously the initial proposal already tried the mild movement/context-squeeze
routine. The Move/squeeze action mostly repeated that same routine, so blocked
results commonly stayed blocked. Unused padding in a prior edit's review crop
also reserved space from the next edit, even where no new text had been drawn.

One Move/squeeze action now tries both stronger passes automatically. Pass 1 can
reduce the current font size to 65% and horizontal width to 75%; if necessary,
pass 2 tries 55% and 65%, respectively. Each pass searches tracking and small
local vertical alignment alternatives, retaining the original caption lane,
bounded horizontal movement and protection of neighboring words. The changed
text can be squeezed in its own box when stale OCR spans or another edited word
prevent borrowing context. Hand-adjusted boxes are retained.

Subsequent edits reserve actual rendered text bounds rather than the entire
padded review crop. Original OCR word boxes and newly rendered text remain
protected. Caption strings and substitution spans remain unchanged by fitting.
Strong compression is level 3 and requires visual review. Fitting never approves
or commits an image. An exhausted search reports its pass, variant count and
limits, directing the user to OCR geometry or the prefilled wording editor.

## Measured comparison

The installed previous renderer was compared with the final staged renderer on
12 generated neutral captions: four layouts in Arial, Arial Bold and Impact,
using actual font/style estimation. Three cases fit before; nine fit after at
most one Move/squeeze click. All six newly fitting cases succeeded in one click,
including two adjacent edits and a longer complete caption line. Three extreme
length expansions stayed blocked rather than overflowing their original lane.
These are fixture results, not a guarantee for every image or OCR result.

Comparison data: `C:\codex\clairevironment\release-output\image-caption-gender-fixer\fit-retry-20261029\fit-comparison-one-click.json`.
Before/after contact sheet (visually inspected): `C:\codex\clairevironment\release-output\image-caption-gender-fixer\fit-retry-20261029\fit-comparison-one-click.png`.

| Font | Layout | Previously fit | Fit after one click |
|---|---|---|---|
| arial.ttf | adjacent | no | yes |
| arial.ttf | phrase | yes | yes |
| arial.ttf | line | no | yes |
| arial.ttf | long-line | no | no |
| arialbd.ttf | adjacent | no | yes |
| arialbd.ttf | phrase | yes | yes |
| arialbd.ttf | line | no | yes |
| arialbd.ttf | long-line | no | no |
| impact.ttf | adjacent | no | yes |
| impact.ttf | phrase | yes | yes |
| impact.ttf | line | no | yes |
| impact.ttf | long-line | no | no |

## Validation

- Complete installed suite: 418 passed, two Windows tray checks failed; zero errors or skips.
- Both failed checks passed on isolated rerun without code changes. The initial
  failures were missing Shell_NotifyIconGetRect rectangles despite successful
  icon registration. No tray code was changed in this release.
- Rerun XML: `C:\codex\clairevironment\release-output\image-caption-gender-fixer\fit-retry-20261029\shell-recheck-1ac753f7ddbf4532a2098b3fed30585e.xml`.
- Duration: 205.402 seconds.
- XML: `C:\codex\clairevironment\release-output\image-caption-gender-fixer\fit-retry-20261029\installed-results-ca2cf1aefc564499bc03184e603ee045.xml`.
- Eight added tests reproduce formerly blocked own-word, full-line and adjacent-edit
  cases; verify automatic escalation, corrected OCR and manual-box fitting;
  verify protective bounds and readable-limit failures; and exercise the actual
  artwork action through proposal regeneration without bypassing approval.
- Existing movement/context, caption-lane and adjustment checks also pass.
- The protected padding test verifies the next edit retains the first edit's ink.
- Source-image hashes remain unchanged before approval and after test rejection.
- Deployed files and sibling replacement backups were verified by SHA-256.
- The project root retains only its launcher and README as regular files.

Restart running ICGF processes to load this update. No OCR model, package, user
image or existing job was changed by deployment.

## Every affected C:\BAT path

Verified sibling backups preceded replacements. The README backup was then moved
to runtime/backups/implementation to keep the root minimal. No permanent deletion.

- **Created**: `C:\BAT\image_caption_gender_fixer\docs\releases\move-squeeze-retries-20261029.md`
- **Modified**: `C:\BAT\image_caption_gender_fixer\README.md`
- **Created; moved to `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610291600.replaced-by-chatgpt.bak`**: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610291600.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610291600.replaced-by-chatgpt.bak`
- **Modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610291600.replaced-by-chatgpt.bak`
- **Modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py.bak.202610291600.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_fit_retries.py`
