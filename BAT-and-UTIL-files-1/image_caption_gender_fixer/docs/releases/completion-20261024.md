# Completion release 0.2.0 — 2026-10-24

The supported Windows CPython 3.10 x64 local PNG/JPEG workflow is implemented
and installed at `C:\BAT\image_caption_gender_fixer`. This report supersedes
the earlier implementation checkpoint; it does not claim perfect reconstruction
of photographic detail or fonts. The root contains only the launcher and README.

## Installed validation

- Full installed suite: **168 passed, zero failures/errors**, JUnit elapsed time
  **39.813 seconds**. XML: `tests\output\results-ec4b0f04d38748b0a66dac2e30475153.xml`.
- Earlier completion runs: 160 full installed cases passed, followed by five
  focused unfinished-session menu cases. The final 168-case run includes those
  five, two end-to-end transparent-PNG cases, and legacy-Windows-code-page UTF-8
  output coverage with accented, Japanese, and emoji text.
- Actual local components were used for OCR/rendering, PNG/JPEG/metadata/alpha,
  safe commit, exact undo, all durable undo recovery boundaries, Windows leases,
  process-death locking, collisions, long Unicode paths, recycling, and private
  package reconstruction/relocation. The 57.9 MB offline archive was really
  extracted, imported, relocated, and tested with NumPy/OpenCV PNG encoding.
- Dependency internet download and installer control paths are mocked in tests.
  Tests do not install global software or access the network. Disk-failure,
  exhaustive font/hardware/network-filesystem behavior, and aesthetic perfection
  are not claimed as tested.
- Actual interactive PTY smoke: both terminal streams were TTYs; native Chafa
  previews and the shared rainbow progress bar ran. A level-1 `good boi` →
  `good girl` proposal still requested approval. Choosing skip returned code 10,
  preserved the original SHA-256, created no history, and recycled all previews.
  The original and corrected proposal were visually inspected. A harness redirected
  job/cache/log state to an isolated temporary directory; no production bypass
  flag was introduced. No real user image was edited.
- Final help, version JSON, doctor JSON, caller-CWD wildcard dry run, rules
  explain JSON, and cleanup dry run JSON all returned success. Complete before/
  after file hashes proved both installation and generated target unchanged.
- `doctor` verified 2,022 required bundled files with no hash errors. Two optional
  original wheel downloads are absent by design after safe recycling. Private
  imports and native versions passed; there were no pending transactions,
  resumable jobs, malformed sessions, retained artifacts, or orphan state staging.
- The bundled `clairecjs_utils.claire_progressbar` matches the current shared
  library byte-for-byte; the shared library and its mirrors were not modified.

## Completion changes

The remaining work strengthened literal/Unicode/scoped/cascaded rules and
exclusions; profiles and saved preferences; post-render OCR correction; blocked
render adjustment; repair comparisons; mask ownership and face/edge/seam warnings;
source/approved-stage identity protection; journal/recovery consistency; undo
fault boundaries; cancellation and old-job selection; JSON contracts; redacted
local diagnostics; ABI/isolation/consent repair; metadata/alpha; read-only doctor
and explain; and complete documentation and dependency notices. The 32-section
acceptance mapping is in `docs/requirements-checklist.md`.

The transparency regression fixed black text whose RGB values equal a transparent PNG's
background. OCR now analyzes an appropriate opaque composite without changing
the source/output alpha. Ink masks also account for alpha, and transparency
forces review uncertainty. Both black and white transparent-background edits
were tested end-to-end, including preserved original bytes and final OCR.
The last command-line acceptance check also exposed ANSI-code-page output on
Windows redirects. Redirected stdout/stderr now use UTF-8, preserving Unicode
JSON text instead of failing while reporting a valid Unicode filename.

## Operation and limits

Use Windows CPython 3.10 x64; Python itself is not bundled. Python packages and
native tools are private and already usable. Healthy use needs no pip command,
environment activation, network, or installation consent. Missing/damaged
dependencies explicitly request consent and explain that correction cannot
continue without the required component. `--yes` does not supply that consent.

The delivered versions are Pillow 10.3.0, NumPy 1.26.4, OpenCV headless 4.10.0.84,
regex 2024.4.16, tqdm 4.66.2, Tesseract 5.5.3.20260724 with pinned English fast
data, Chafa 1.18.2, ImageMagick 7.1.1-10, and 7-Zip 23.01. Exact origins, hashes,
notices, locations, and rebuild instructions are in `docs/bundled-dependencies.md`,
`environment/requirements.lock`, `environment/manifest.json`, and
`environment/metadata/provenance.json`.

All analysis is local. Renders/crops/masks/staging are adjacent to the image;
hidden unencrypted `.history.icgf` travels with its folder. Originals are renamed
to timestamped sibling backups and never deleted by correction. Undo archives
the corrected file before restoring the original exactly. Every proposal needs
approval by default; uncertainty and blocked fits never silently auto-approve.

Animation/multiframe and unvalidated formats explicitly defer. Font/style and
photographic reconstruction are best-effort and require inspection. JPEG is
lossy; PNG outside-region pixel preservation is validated. Face/edge warnings are
heuristics. Live-job/cross-computer undo and remote-filesystem durability are not
promised; folder history itself is portable. Optional neural models/perceptual
auto-skip were not selected.

## Space and recycling

The earlier cleanup recycled exactly **107,671,736 bytes (107.7 MB decimal)** of
four verified redundant setup downloads. It preserved installed dependencies and
the complete offline repair ZIP. Cleanup runs after successful install/repair and
processing startup, keeps unknown/changed/linked/busy files, and has no permanent
deletion fallback. See `setup-download-cleanup-20261024.md` for those exact paths.
Items in the Recycle Bin still consume drive space until it is emptied separately.

Completion-pass code/docs/tests and mandatory replacement backups add storage;
the inventory below measures the final tool folder, including those backups and
test reports. It excludes the Recycle Bin and generated disposable test trees.

- Before this completion pass: **482,109,245 bytes**.
- Final folder: **482,629,979 bytes**, including this report; **2,183 files**.
- Net addition for this pass: **520,734 bytes**.
- Compared with the original pre-cleanup 589,313,483-byte folder: **106,683,504 bytes smaller**.

## Every affected C:\BAT file path

This is the complete file-level difference from the recorded pre-completion
inventory, plus the two temporary sibling backup names moved out of the root.
Created replacement backups were verified before any existing content changed.
Nothing in the pre-completion inventory was permanently deleted.

Created: **61**. Modified: **12**. Deleted: **0**. Two transient root backups were renamed as listed below.

| Action | Full affected path | Final bytes |
| --- | --- | ---: |
| Created | `C:\BAT\image_caption_gender_fixer\docs\bundled-dependencies.md` | 5232 |
| Modified | `C:\BAT\image_caption_gender_fixer\docs\implementation-status.md` | 3410 |
| Created | `C:\BAT\image_caption_gender_fixer\docs\implementation-status.md.bak.202610241534.replaced-by-chatgpt.bak` | 4924 |
| Created | `C:\BAT\image_caption_gender_fixer\docs\json-and-exit-codes.md` | 2544 |
| Created | `C:\BAT\image_caption_gender_fixer\docs\licenses\chafa-AUTHORS.txt` | 1754 |
| Created | `C:\BAT\image_caption_gender_fixer\docs\licenses\chafa-COPYING.LESSER.txt` | 7652 |
| Created | `C:\BAT\image_caption_gender_fixer\docs\licenses\chafa-COPYING.txt` | 35149 |
| Created | `C:\BAT\image_caption_gender_fixer\docs\licenses\sources.json` | 1136 |
| Created | `C:\BAT\image_caption_gender_fixer\docs\licenses\tessdata-fast-LICENSE.txt` | 11358 |
| Created | `C:\BAT\image_caption_gender_fixer\docs\recovery.md` | 7056 |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\completion-20261024.md` | This report |
| Created | `C:\BAT\image_caption_gender_fixer\docs\requirements-checklist.md` | 9277 |
| Modified | `C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py` | 2796 |
| Modified | `C:\BAT\image_caption_gender_fixer\README.md` | 14988 |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\image_caption_gender_fixer.py.bak.202610241534.replaced-by-chatgpt.bak` | 2319 |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610241534.replaced-by-chatgpt.bak` | 6270 |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\__init__.py` | 97 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\__init__.py.bak.202610241534.replaced-by-chatgpt.bak` | 97 |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py` | 63911 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610241534.replaced-by-chatgpt.bak` | 48052 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610241556.replaced-by-chatgpt.bak` | 63566 |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py` | 7845 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py.bak.202610241534.replaced-by-chatgpt.bak` | 7362 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\diagnostics.py` | 3804 |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\errors.py` | 696 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\errors.py.bak.202610241534.replaced-by-chatgpt.bak` | 347 |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\fs.py` | 11042 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\fs.py.bak.202610241534.replaced-by-chatgpt.bak` | 10758 |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py` | 27249 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py.bak.202610241534.replaced-by-chatgpt.bak` | 22573 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py.bak.202610241551.replaced-by-chatgpt.bak` | 26431 |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\rules.py` | 15648 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\rules.py.bak.202610241534.replaced-by-chatgpt.bak` | 10060 |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\sessions.py` | 4546 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\sessions.py.bak.202610241534.replaced-by-chatgpt.bak` | 2893 |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\transactions.py` | 16149 |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\transactions.py.bak.202610241534.replaced-by-chatgpt.bak` | 12208 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_approval_integrity.py` | 1374 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_completion.py` | 15197 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_contracts.py` | 3968 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_final_contracts.py` | 3740 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_invalid_rule_bytes.py` | 500 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_metadata_details.py` | 1324 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_output_encoding.py` | 1047 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_review_and_platform.py` | 7482 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_state_staging.py` | 887 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_transparent_ocr.py` | 1363 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_undo_recovery.py` | 2515 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-completion-ec5a8ef1096f4a74ae23f700c6211941\.gitignore` | 39 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-completion-ec5a8ef1096f4a74ae23f700c6211941\CACHEDIR.TAG` | 191 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-completion-ec5a8ef1096f4a74ae23f700c6211941\README.md` | 310 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-completion-ec5a8ef1096f4a74ae23f700c6211941\v\cache\nodeids` | 13995 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-completion-ec5a8ef1096f4a74ae23f700c6211941\v\cache\stepwise` | 2 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-04cd2118ba0841c289b2850243284c33\.gitignore` | 39 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-04cd2118ba0841c289b2850243284c33\CACHEDIR.TAG` | 191 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-04cd2118ba0841c289b2850243284c33\README.md` | 310 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-04cd2118ba0841c289b2850243284c33\v\cache\nodeids` | 14836 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-04cd2118ba0841c289b2850243284c33\v\cache\stepwise` | 2 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-d486ca55b1764692aab2de3589993bca\.gitignore` | 39 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-d486ca55b1764692aab2de3589993bca\CACHEDIR.TAG` | 191 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-d486ca55b1764692aab2de3589993bca\README.md` | 310 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-d486ca55b1764692aab2de3589993bca\v\cache\nodeids` | 14735 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-final-d486ca55b1764692aab2de3589993bca\v\cache\stepwise` | 2 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-old-job-acceptance-64f5d513f1e04938b399703921559246\.gitignore` | 39 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-old-job-acceptance-64f5d513f1e04938b399703921559246\CACHEDIR.TAG` | 191 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-old-job-acceptance-64f5d513f1e04938b399703921559246\README.md` | 310 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-old-job-acceptance-64f5d513f1e04938b399703921559246\v\cache\nodeids` | 501 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-old-job-acceptance-64f5d513f1e04938b399703921559246\v\cache\stepwise` | 2 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\results-5c6362f4d1004c898778f689bc13c7be.xml` | 20636 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\results-bebb0203749147da9a971a7428fdb8c5.xml` | 19658 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\results-ec4b0f04d38748b0a66dac2e30475153.xml` | 20771 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\results-f9a4c6a3b2f3442b833676d1438e3c76.xml` | 884 |
| Created | `C:\BAT\image_caption_gender_fixer\tests\unit\test_old_sessions.py` | 2062 |

The root's required sibling replacement backups existed under these transient
names before being moved into the implementation-backup directory. Both original
content and backups were preserved; collision numbering was available.

| Action | Transient path | Final path |
| --- | --- | --- |
| Created, then renamed | `C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py.bak.202610241534.replaced-by-chatgpt.bak` | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\image_caption_gender_fixer.py.bak.202610241534.replaced-by-chatgpt.bak` |
| Created, then renamed | `C:\BAT\image_caption_gender_fixer\README.md.bak.202610241534.replaced-by-chatgpt.bak` | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610241534.replaced-by-chatgpt.bak` |

## Deployed source hashes

| File | SHA-256 |
| --- | --- |
| `C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py` | `a555146b7bb3a7d93b9ac8e3dae5f8af06d70ac3a3e3f23017218418721cac42` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\__init__.py` | `f8f33f7588201a9ad0ff94cd1324da95ecc521b1d9aa2ba7742546eed4b8361e` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py` | `6f74920691e0a5b3582f91620fde4a457cff0385f775ce8b056d9b1aa33d8266` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py` | `767407a00b617e8bb434b6df0f16397fcc513f0036fa9f526b418e6cc665c12a` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\diagnostics.py` | `d53ba871f973fab0cc395cf3ed6823d81307af4e67f79dc253e1d09b24909ad2` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\errors.py` | `bb8ba4bb40444699e0f70ebebd3061021dcc31020b969422523d4d86854ceb70` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\fs.py` | `9e0b02e1eb8961fd1a521c43f8c9647b84cfaf0948fde4e2ef9e8f80c1f02661` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py` | `01a0f1ecd4cc50b7621df30c53a4d741b51e741fcf22931639a5af5f33730783` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\rules.py` | `56810b97da9ecf4911a51174de209fc79eea06a887e7223370fd001bbb4a672f` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\sessions.py` | `c4a7f07e4d99430166370efc934d47ab4392764c3fdc93a74b274ea269d5ca2a` |
| `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\transactions.py` | `7865921b4b05eb908881e53cb5030442fc2c1390d23aeef38bf117ddfd9169d0` |

## Raw read-only command evidence

This snapshot precedes creation of this release report, so its file/byte count
excludes this report. All commands returned zero, and complete before/after
inventories were identical. The caller target was a generated disposable image.

```json
{
  "root": "C:\\BAT\\image_caption_gender_fixer",
  "python": "C:\\ProgramData\\anaconda3\\python.exe",
  "caller_cwd": "C:\\Users\\ClioC\\AppData\\Local\\Temp\\ICGF-TTYSmoke-06e3d66546b24481a580b9ec02db744c\\images",
  "read_only_installation_unchanged": true,
  "read_only_target_unchanged": true,
  "installation_file_count": 2182,
  "installation_bytes": 482602224,
  "root_files": [
    "README.md",
    "image_caption_gender_fixer.py"
  ],
  "shared_progress_sha256": "212081f8d27717d5658e4a4cc398551e8450d42d2f3a0e5203b40c6852779b8e",
  "commands": [
    {
      "arguments": [
        "--help"
      ],
      "exit_code": 0,
      "seconds": 0.234,
      "stderr": "",
      "stdout": "usage: image_caption_gender_fixer.py [--help] [--version] [--dry-run]\n                                     [--recursive] [--include-hidden]\n                                     [--include-system] [--yes] [--json]\n                                     [--no-preview] [--eco] [--verbose]\n                                     [--new-session]\n                                     [--review-no-match-images]\n                                     [--allow-network]\n                                     [--recover-from-backups] [--global-rules]\n                                     [--regex]\n                                     [--skip-reivew-for-confident-ones]\n                                     [--ask-about-undo-archives | --keep-undo-archives | --recycle-undo-archives]\n                                     [--resume [RESUME]] [--profile PROFILE]\n                                     [--priority PRIORITY]\n                                     [--scope {folder,global}]\n                                     [--case {transfer,exact,ignore}]\n                                     [--punctuation {exact,whitespace,flex}]\n                                     [--literal-path LITERAL_PATH]\n                                     [--context CONTEXT]\n                                     [--image-hash IMAGE_HASH]\n                                     [--session-id SESSION_ID]\n                                     [--occurrence OCCURRENCE] [--all-future]\n                                     [--note NOTE]\n                                     [items ...]\n\nLocal reviewed image text correction. Originals are preserved; history lives\nin hidden .history.icgf.\n\npositional arguments:\n  items\n\noptions:\n  --help\n  --version\n  --dry-run\n  --recursive\n  --include-hidden\n  --include-system\n  --yes\n  --json\n  --no-preview\n  --eco\n  --verbose\n  --new-session\n  --review-no-match-images\n  --allow-network\n  --recover-from-backups\n  --global-rules\n  --regex\n  --skip-reivew-for-confident-ones, --skip-review-for-confident-ones\n  --ask-about-undo-archives\n  --keep-undo-archives\n  --recycle-undo-archives\n  --resume [RESUME]\n  --profile PROFILE\n  --priority PRIORITY\n  --scope {folder,global}\n  --case {transfer,exact,ignore}\n  --punctuation {exact,whitespace,flex}\n  --literal-path LITERAL_PATH\n  --context CONTEXT\n  --image-hash IMAGE_HASH\n  --session-id SESSION_ID\n  --occurrence OCCURRENCE\n  --all-future\n  --note NOTE\n\nCommands: doctor; rules show/add/disable/enable/explain; history\nstatus/verify/backup; environment status/repair/cleanup; sessions\nlist/status/abandon; preferences show/set/reset; undo; recover; explain.\n\n"
    },
    {
      "arguments": [
        "--version",
        "--json"
      ],
      "exit_code": 0,
      "seconds": 0.204,
      "stderr": "",
      "result": {
        "version": "0.2.0",
        "schema_versions": {
          "program": "0.2.0",
          "rules": 1,
          "metadata_marker": 1,
          "folder_history": 1,
          "sessions": 1,
          "transactions": 1,
          "preferences": 1,
          "bundle": 1
        }
      }
    },
    {
      "arguments": [
        "doctor",
        "--json"
      ],
      "exit_code": 0,
      "seconds": 4.546,
      "stderr": "",
      "result": {
        "root": "C:\\bat\\image_caption_gender_fixer",
        "unexpected_items": [],
        "missing_root_files": [],
        "pre_existing_at_inspection": [],
        "introduced_by_doctor": [],
        "bundle": {
          "checked": 2022,
          "optional_absent": [
            "wheels/numpy-1.26.4-cp310-cp310-win_amd64.whl",
            "wheels/opencv_python_headless-4.10.0.84-cp37-abi3-win_amd64.whl"
          ],
          "errors": []
        },
        "environment": {
          "native": {
            "tesseract": {
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\tools\\tesseract\\tesseract.exe",
              "version": "tesseract v5.5.3.20260724"
            },
            "magick": {
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\tools\\magick\\magick.exe",
              "version": "Version: ImageMagick 7.1.1-10 Q16-HDRI x64 fa1d7e6:20230521 https://imagemagick.org"
            },
            "chafa": {
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\tools\\chafa\\chafa.exe",
              "version": "Chafa version 1.18.2"
            }
          },
          "english_fast": true,
          "packages": {
            "PIL": {
              "version": "10.3.0",
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\packages\\PIL\\__init__.py"
            },
            "numpy": {
              "version": "1.26.4",
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\packages\\numpy\\__init__.py"
            },
            "cv2": {
              "version": "4.10.0",
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\packages\\cv2\\__init__.py"
            },
            "regex": {
              "version": "2.5.141",
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\packages\\regex\\__init__.py"
            },
            "pytest": {
              "version": "7.4.0",
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\packages\\pytest\\__init__.py"
            },
            "tqdm": {
              "version": "4.66.2",
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\packages\\tqdm\\__init__.py"
            },
            "clairecjs_utils.claire_progressbar": {
              "version": null,
              "path": "C:\\bat\\image_caption_gender_fixer\\environment\\packages\\clairecjs_utils\\claire_progressbar.py"
            }
          }
        },
        "pending_transactions": [],
        "state_staging_retained": [],
        "resumable_sessions": [],
        "session_issues": [],
        "retained_artifacts": []
      }
    },
    {
      "arguments": [
        "*.png",
        "--dry-run",
        "--json"
      ],
      "exit_code": 0,
      "seconds": 0.813,
      "stderr": "",
      "result": {
        "state": "dry_run",
        "results": [
          {
            "file": "C:\\Users\\ClioC\\AppData\\Local\\Temp\\ICGF-TTYSmoke-06e3d66546b24481a580b9ec02db744c\\images\\generated caption é.png",
            "state": "dry_run",
            "proposed_regions": 1,
            "review_required": true
          }
        ],
        "resumable_sessions": []
      }
    },
    {
      "arguments": [
        "rules",
        "explain",
        "good boi",
        "--json"
      ],
      "exit_code": 0,
      "seconds": 0.25,
      "stderr": "",
      "result": {
        "source": "good boi",
        "final": "good girl",
        "edits": [
          {
            "start": 0,
            "end": 8,
            "before": "good boi",
            "after": "good girl"
          }
        ],
        "trace": [
          {
            "rule": "builtin-0",
            "priority": 100,
            "before": "boi",
            "after": "boy",
            "original_span": [
              5,
              8
            ]
          },
          {
            "rule": "builtin-1",
            "priority": 10,
            "before": "good boy",
            "after": "good girl",
            "original_span": [
              0,
              8
            ]
          }
        ],
        "shadowed": [
          {
            "rule": "builtin-2",
            "span": [
              5,
              8
            ],
            "priority": 10
          }
        ],
        "stages": [
          {
            "priority": 100,
            "before": "good boi",
            "after": "good boy",
            "selected_rules": [
              "builtin-0"
            ]
          },
          {
            "priority": 10,
            "before": "good boy",
            "after": "good girl",
            "selected_rules": [
              "builtin-1"
            ]
          }
        ]
      }
    },
    {
      "arguments": [
        "environment",
        "cleanup",
        "--dry-run",
        "--json"
      ],
      "exit_code": 0,
      "seconds": 0.219,
      "stderr": "",
      "result": {
        "state": "dry_run",
        "setup_cleanup": {
          "recycled": [],
          "retained": [],
          "would_recycle": [],
          "recycled_bytes": 0,
          "eligible_bytes": 0
        }
      }
    }
  ]
}
```

Interactive smoke completion record:

```json
{
  "exit_code": 10,
  "original_unchanged": true,
  "history_created": false,
  "remaining_previews": []
}
```
