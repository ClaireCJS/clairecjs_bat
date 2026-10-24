# Implementation checkpoint

The current release location is `C:\BAT\image_caption_gender_fixer`.
This supersedes the earlier nested `image_caption\gender_fixer` location.
Only `image_caption_gender_fixer.py` and `README.md` belong directly in the root.
The entire project, including development files and preserved backups, travels
with the directory. Historical backups and test reports retain their original
contents and may mention earlier paths.

The complete specification is in `docs/implementation-specification.txt`.
This remains a development release; a directory move does not certify every
requirement in the 32-section specification as complete.

## Dependency bundle

- Supported interpreter: CPython 3.10 x64; Python itself is not bundled.
- Launcher starts isolated, selects private packages, and disables bytecode.
- Pillow 10.3.0, NumPy 1.26.4, OpenCV headless 4.10.0.84, regex, tqdm,
  shared Claire progress-bar module, pytest and test dependencies are included.
- NumPy/OpenCV downloads were explicitly approved and checked against PyPI hashes.
- Tesseract and English fast data downloads were explicitly approved. The system
  Chocolatey attempt installed no packages; verified private archive extraction
  supplied the bundled OCR engine instead.
- Tesseract 5.5.3.20260724, English fast data, Chafa 1.18.2,
  ImageMagick 7.1.1-10, and 7-Zip 23.01 are bundled under environment.
- Offline package repair archive, version lock and per-file hash manifest are
  kept under environment. Normal users do not need pip or environment setup.
- Existing global Python packages and the shared progress library are unchanged.
- The pre-release cache containing generated-test hashes is preserved under
  runtime/backups/pre-release-test-cache, outside the active cache location.

## Implemented behavior and evidence

- Priority cascade, Unicode word matching, overlap precedence, bounded regex,
  provenance traces, learned folder rules and profiles.
- Hidden unencrypted folder history with relative names, hashes, chained records,
  corruption detection and committed/undone transaction states.
- Windows read/delete leases, verified non-overwriting renames, original backups,
  local durable journals, rollback, recovery, and byte-exact undo.
- Windows IFileOperation recycling; no permanent-delete fallback.
- Real local OCR and classical PNG/JPEG rendering, masks, font candidates,
  text fitting, neighboring-text protection, adjacent hidden review artifacts.
- Mandatory review, adjustments, optional OCR correction, level 1 bypass aliases,
  and no review bypass through --yes.
- Sessions, skip/defer handling, dry-run, rules/history/preferences commands,
  corrected-hash cache, and owned-artifact cleanup.
- Prior completed suite: 73 tests passed, including real PNG/JPEG OCR,
  transactions, collision handling, interruption recovery, history, undo and
  recycling. Dependency-installation tests are mocked and never download.
- Relocation tests additionally exercise the launcher from an unrelated working
  directory with a minimal PATH, assert private package/native paths, verify the
  two-file root, and run bundled Chafa on a generated image.
- See docs/releases for the actual post-move test result and the complete list
  of created C:\BAT file paths. No real user images are used for validation.

## Work still requiring implementation or broader verification

- Full 32-section requirement-by-requirement acceptance checklist and recovery
  documentation; do not treat this checkpoint as that checklist.
- More image-layout tests: multiple regions, edge fitting, alpha/orientation,
  outside-region pixel preservation, detailed manual-adjustment behavior.
- Broader session resume/forget/preference tests and corruption-boundary audits.
- Full package-repair end-to-end validation and optional manifest-based doctor
  health checks (doctor currently checks root cleanliness and reports imports).
- More learned-ignore scope/context controls and profile administration.
- Crash-report/logging coverage and automatic face/strong-edge warnings.
- Font/effect inference for complex captions. Photograph repair remains
  approximate and requires review. Animated/multiframe inputs are deferred;
  PNG/JPEG are the implemented output formats.
- Review redistribution notices for all bundled native distributions before
  distributing this development build beyond the current local installation.

## Development safety

Before replacing an existing file, create and verify the required timestamped
sibling replacement backup. Keep root-file backups in runtime/backups after
verification. Preserve originals and uncertain artifacts; recycle rather than
permanently deleting. Never test on real user images. Disclose every C:\BAT file
change, including deployment, test reports, backups and synchronization.

```powershell
python -B -I -S C:\BAT\image_caption_gender_fixer\tests\run_tests.py -q
```