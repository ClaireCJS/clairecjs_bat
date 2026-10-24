# Image Caption Gender Fixer

Windows image-caption correction with local OCR, per-image review, preserved
originals, and hidden history beside the images.

The project now lives at **`C:\BAT\image_caption_gender_fixer`**. The launcher
and this README are the only regular files in the project root. Source,
dependencies, tests, documentation, backups, and runtime state stay in their
respective subdirectories. Resource paths are relative to the launcher, so the
whole directory can be moved together.

## Run

Use **64-bit CPython 3.10**. Python itself is a prerequisite; the required Python
packages, OCR engine, English OCR data, terminal renderer, and image tools are
included under `environment`. The launcher isolates the application from global
Python packages. No pip command or environment activation is needed.

Run these commands from the folder containing the images:

```powershell
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py --help
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py doctor
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py '*.png' --dry-run --json
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py 'image.jpg'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py '*'
```

Quote wildcard arguments in PowerShell. `--recursive` opts into subfolders.
`--no-preview` disables terminal images while retaining the review questions.
The tool refuses to process images inside its own installation directory.

The built-in rules include `boi` → `boy`, then `good boy` → `good girl`,
`boy` → `girl`, `man` → `woman`, and `husband` → `wife`. For example,
`good boi` becomes `good girl` through the priority cascade. Folder rules are
stored in `.image-gender-fixer.stt`; use `rules show` and `rules explain TEXT`
to inspect the rule set and its trace.

## Review and files

Every proposed correction requires review by default, including high-confidence
renders. `--yes` does not bypass that review or dependency consent. The opt-in
`--skip-review-for-confident-ones` flag bypasses only level 1 proposals; the
original spelling `--skip-reivew-for-confident-ones` is also accepted.

Proposals, masks, and other review images are hidden files beside the source.
On approval, the original is preserved under a sibling name such as
`image.jpg.bak.202610240845.replaced-by-chatgpt.bak`. The corrected image is
written separately as `image-gendeerfixed.jpg` (the suffix is intentional).
Collisions receive numbered names; existing files are preserved.

The hidden, unencrypted `.history.icgf` in each image folder records relative
filenames and hashes. Keep that file with the folder when moving or renaming it.
Local resumable-job state and undo across computers are not portability promises.

## Resume, undo, and recovery

```powershell
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py sessions list
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py --resume
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py undo 'image-gendeerfixed.jpg'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py undo '*' --keep-undo-archives
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py history verify .
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py recover --dry-run --json
```

Undo restores the original bytes and preserves the corrected image as an undo
archive. The default asks whether to keep or recycle that archive; an archive
changed after conversion is kept unless explicitly approved for recycling.
Recovery stops if history integrity or file ownership cannot be established.
Retain originals, backups, journals, and history when investigating a failure.
Forgetting an unfinished session does not undo completed conversions.

Missing OCR components trigger an explicit installation question explaining that
image correction cannot proceed without consent. Private Python-package repair
uses the bundled offline archive and asks for confirmation. Neither `--yes` nor
JSON mode approves installation automatically. Inspect `environment status` or
run `environment repair` interactively when needed.

Recognized setup downloads are recycled automatically when normal image
processing starts and after a successful dependency installation or repair.
Cleanup verifies the installed replacements and each archive's exact hash.
Changed, unknown, linked, busy, or still-needed files are kept. The working
packages and `environment/wheels/runtime-bundle.zip` remain available for
portable operation and offline repair.

Run `environment cleanup --dry-run --json` to inspect eligible downloads or
`environment cleanup --json` to clean them immediately. Help, version, dry-run,
and read-only inspection commands do not trigger automatic cleanup. Cleanup
reports the bytes removed from the project directory. Recycled downloads still
occupy space in Windows' Recycle Bin until it is emptied separately.

## Project files and verification

| Directory | Contents |
| --- | --- |
| `src` | Application modules |
| `environment` | Private packages, native tools, OCR data, repair archive, hashes |
| `runtime` | Local state, cache, and preserved implementation backups |
| `tests` | Unit/integration tests and reports |
| `docs` | Full specification, implementation status, and release disclosure |

Run the isolated test suite with the supported Python interpreter:

```powershell
python -B -I -S C:\BAT\image_caption_gender_fixer\tests\run_tests.py -q
```

Tests generate their own images outside the installation. Native OCR, Windows
file transactions, byte-exact undo, and recycling are exercised; dependency
download tests use mocks.

This is a development release. PNG and JPEG are the implemented output formats;
animated/multiframe inputs are deferred. Complex photographic repairs can need
manual adjustment and remain subject to review. See
[implementation status](docs/implementation-status.md) for remaining work and
[the full specification](docs/implementation-specification.txt) for the target
behavior. Relocation verification and the complete list of created `C:\BAT`
paths are recorded under `docs/releases`.
