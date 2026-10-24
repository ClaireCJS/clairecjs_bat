# Automatic setup-download cleanup — 2026-10-24

Implemented in `src/image_caption_gender_fixer/maintenance.py`, with startup integration in `cli.py` and successful-install integration in `dependencies.py`. Private-package repair also cleans only after verification and publication of a ready environment.

Normal image-processing startup and environment repair automatically inspect an exact filename allowlist. Each candidate must have the pinned archive hash, be an ordinary unlinked file on checked paths, and permit a read/delete lease that excludes active writers. Private replacements must verify first: NumPy/OpenCV import and perform PNG encoding using the selected private package tree, with an intact offline repair archive; Tesseract must be private and verify the pinned English data plus available language probe. Unknown, changed, busy, linked, or unverified downloads stay in place. Recycle Bin failures retain files with no permanent-deletion fallback.

The installed packages, native tools, OCR data, offline `runtime-bundle.zip`, originals, image backups, and undo archives are retained. `environment cleanup --dry-run --json` inspects the candidates; `environment cleanup --json` runs cleanup explicitly. Help, version, dry runs, and read-only status/inspection commands do not automatically mutate the installation. The environment manifest marks original wheel downloads as optional.

## Measured result

| Measurement | Bytes | Decimal MB |
| --- | ---: | ---: |
| Immediately before real startup cleanup | 589751520 | 589.752 |
| Immediately after real startup cleanup | 482079784 | 482.080 |
| Downloads removed from the project | 107671736 | 107.672 |

The reduction is 107,671,736 bytes (102.684 MiB). Files were moved to the Windows Recycle Bin, where they still consume drive space until the bin is emptied separately. Subsequent test reports, code changes, required replacement backups, and this disclosure add a small amount to the final project size. No bin-emptying or permanent deletion was performed.

## Verification

- 24 focused cleanup tests passed before deployment, including a real Windows recycle operation while the download lease was held.
- Full suite before actual removal: **101 passed in 10.60 seconds**.
- Installed dry run identified exactly four files and changed no project bytes.
- Installed normal startup against an empty generated target recycled exactly those four files. No real user images were processed.
- Second installed startup was a no-op; the offline repair archive retained its original SHA-256.
- Doctor passed afterward, including private-package imports and the minimal root check.
- Full suite after actual removal: **101 passed in 10.68 seconds**, including real OCR/image correction/undo and relocation/offline repair checks.

## Every affected C:\BAT file

Existing content was backed up under the required timestamped naming convention and SHA-256 verified before replacement. The table lists every final created, modified, or recycled C:\BAT file, including test reports/cache, plus this report. The temporary root README backup rename is recorded separately below.

| Action | Absolute path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Modified | `C:\BAT\image_caption_gender_fixer\environment\build_bundle.py` | 5701 | `351725c7fbf324a1b61e00ebe9187bea72b7677bc540765f22f3b21eb85ca648` |
| Deleted from project (recycled) | `C:\BAT\image_caption_gender_fixer\environment\wheels\opencv_python_headless-4.10.0.84-cp37-abi3-win_amd64.whl` | 38754031 | `afcf28bd1209dd58810d33defb622b325d3cbe49dcd7a43a902982c33e5fad05` |
| Deleted from project (recycled) | `C:\BAT\image_caption_gender_fixer\environment\wheels\numpy-1.26.4-cp310-cp310-win_amd64.whl` | 15808905 | `b97fe8060236edf3662adfc2c633f56a08ae30560c56310562cb4f95500022d5` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\unit\test_maintenance.py` | 11085 | `24f1a51eed5ed943b47086558e3c3c5dce634e97b0a389c10eaf46db7a531877` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\results-f2a59879dbc744288aaf3cc16fe3bcc1.xml` | 11722 | `68f0a172d2216f796c4bd95c5df1fb30f8e64676a9d14e1196e13ca76f8ae484` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\results-07039d995f5e47c1a6d3732c0d74f108.xml` | 11722 | `4fe14a168743f66861b500e73c4e19fb865acee93b4f89b6edd17d22206358e7` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-setup-cleanup-4d8c9cad4e2c49709003f97c9102aed8\v\cache\stepwise` | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-setup-cleanup-4d8c9cad4e2c49709003f97c9102aed8\v\cache\nodeids` | 8065 | `a45e01ce88b17b98e569a508e0b7de4e7a2d3541994f968971e6a784ac5a11d1` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-setup-cleanup-4d8c9cad4e2c49709003f97c9102aed8\README.md` | 310 | `420e808d79a6c25d3cda0af33bc4782314a14949866682c68ce8149e89b66b70` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-setup-cleanup-4d8c9cad4e2c49709003f97c9102aed8\CACHEDIR.TAG` | 191 | `37dc88ef9a0abeddbe81053a6dd8fdfb13afb613045ea1eb4a5c815a74a3bde4` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-setup-cleanup-4d8c9cad4e2c49709003f97c9102aed8\.gitignore` | 39 | `e7c6bb30148cf667606dcd63e7ca77acaa3cfb0c8303bf09e6419e1e1669dc6d` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-after-setup-cleanup-83ddbd2e97544c229e318b136ca0effe\v\cache\stepwise` | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-after-setup-cleanup-83ddbd2e97544c229e318b136ca0effe\v\cache\nodeids` | 8065 | `a45e01ce88b17b98e569a508e0b7de4e7a2d3541994f968971e6a784ac5a11d1` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-after-setup-cleanup-83ddbd2e97544c229e318b136ca0effe\README.md` | 310 | `420e808d79a6c25d3cda0af33bc4782314a14949866682c68ce8149e89b66b70` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-after-setup-cleanup-83ddbd2e97544c229e318b136ca0effe\CACHEDIR.TAG` | 191 | `37dc88ef9a0abeddbe81053a6dd8fdfb13afb613045ea1eb4a5c815a74a3bde4` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\output\cache-after-setup-cleanup-83ddbd2e97544c229e318b136ca0effe\.gitignore` | 39 | `e7c6bb30148cf667606dcd63e7ca77acaa3cfb0c8303bf09e6419e1e1669dc6d` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\maintenance.py` | 7452 | `f25eb0718332b8e67836c399a521bca85b7238eed08e6991a86460c10f1ea022` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py.bak.202610241040.replaced-by-chatgpt.bak` | 7238 | `34897f8ecb1102b0145d7d8d7de0409e93263fa3a4048160d99e92eff8dc57fd` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py` | 7362 | `221117a765bcd725d20d9285dc0ec69dc84549f006dd458093729eb6e27bbb0a` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610241040.replaced-by-chatgpt.bak` | 47196 | `7ac50c25f3e9da05770cd2210b021fb774cf4bf5aa756bed8a5be83fb258ac52` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py` | 48052 | `2def36d71eb0a7c7933fac6a281a370fb20d34b9cae40aa18818f798dd7bfd28` |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610241040.replaced-by-chatgpt.bak` | 5476 | `4417cd7f16d9192e94f9dc530637a13759672f6346c26f0a0cb9397735109ef7` |
| Modified | `C:\BAT\image_caption_gender_fixer\README.md` | 6270 | `54d5facd2ccd2ef1c956be55ea4604323540601c778459f19571fe1d2a204181` |
| Created | `C:\BAT\image_caption_gender_fixer\environment\manifest.json.bak.202610241040.replaced-by-chatgpt.bak` | 331632 | `6dd247e3bdaa911924ccb0fa7639e2d8e677fa37e7d12cebf13524bec15aa49e` |
| Modified | `C:\BAT\image_caption_gender_fixer\environment\manifest.json` | 331786 | `705abb929b01dcbfdaa482099ea47de7980f1bb6e01628cf1fbac0dd7df7fef8` |
| Created | `C:\BAT\image_caption_gender_fixer\environment\build_bundle.py.bak.202610241040.replaced-by-chatgpt.bak` | 5573 | `11677d14d664631ef4877b9afebbf053d5a430661e5e2846abd17b0ad7bf9f72` |
| Deleted from project (recycled) | `C:\BAT\image_caption_gender_fixer\environment\staging\tesseract.5.5.3.20260724.nupkg` | 26535576 | `d59129139ae1b2b8abd0474b4526670e3907e81718dc0ae3a2b9fd4ae0805967` |
| Deleted from project (recycled) | `C:\BAT\image_caption_gender_fixer\environment\staging\tesseract-ocr-w64-setup-5.5.3.20260724.exe` | 26573224 | `bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\setup-download-cleanup-20261024.md` | This report | Self-hash omitted |

- Created, then renamed: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610241040.replaced-by-chatgpt.bak` → `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610241040.replaced-by-chatgpt.bak`. This is the verified README backup moved into runtime/backups/implementation to retain the two-file root.
