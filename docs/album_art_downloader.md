# album_art_downloader.py

`album_art_downloader.py` scans a music tree, identifies releases through MusicBrainz, retrieves their images from Cover Art Archive, and writes verified artwork sidecars. Its defaults encode the artwork workflow developed for `C:\new\music` and `C:\soulseek`.

Documentation maintenance: keep `album_art_downloader.md` beside the main script and synchronize the same content to `C:\BAT\docs\album_art_downloader.md` on every documentation update. Keep both Markdown copies synchronized in the repository too. Before replacing an existing copy, create and verify the required timestamped sibling backup. Program releases continue to increment by one and retain a descriptive versioned `.py` snapshot.

## Performance improvements (v39)

Scanning now lists each included directory once and prunes excluded subtrees before walking them. The excluded-directory count therefore counts pruned subtree roots, not every folder underneath them. Eligible folders retain their deterministic ordering.

The default `--search-strategy smart` stops broader fallback searches when artist, album, available year, and track count match exactly. Detail lookups can also stop when a candidate has a track listing and a score of at least 99. These are matching heuristics, not a guarantee of the correct edition. Use `--search-strategy exhaustive` to search every fallback and fetch the requested number of candidate details. If image review exhausts the shortened candidate list with `retry`, the remaining searches run automatically.

Repeated artwork hashes are cached per folder with file-metadata invalidation; final replacement checks still read the target afresh. MISC sidecars reuse image conversion for targets of the same format instead of converting once per track. Resume journals are read line by line, and Cover Art Archive responses no longer incur an unconditional pause. MusicBrainz request spacing and network retry/backoff remain enforced.

Controlled regression fixtures reduce metadata requests from six to two for a strong match, and require only three encoding calls for ten same-format track sidecars. Actual savings depend on the library and matching results. All 62 internal tests pass for this release.

## Single-file dependency setup (v38)

You can distribute just `album_art_downloader.py`. Python 3.10 or newer must already be installed; the script cannot install the interpreter needed to start itself. First-time dependency installation requires internet access. The Markdown and preferences sidecars are optional.

On startup, the script checks for `requests`, Pillow, `mutagen`, and `send2trash`. It reuses working installed packages. If packages are missing, it first checks for a working private environment, then creates one if needed under `%LOCALAPPDATA%\album_art_downloader\runtime\python` on Windows. It installs packages from PyPI using that environment's pip and restarts the same single script with the original arguments and working directory. Global Python packages and the system PATH are not modified. New installs use requests 2.x, Pillow 10–12.x, mutagen 1.47–1.x, and Send2Trash 1.8–2.x; existing working packages are not automatically upgraded.

Visual review also checks Chafa. An existing working `chafa` on PATH or an explicit `--chafa-command` is reused. On Windows x64, a missing default Chafa is downloaded into the private runtime directory from the publisher, checked against a pinned SHA-256 hash, safely unpacked, and tested with `--version`. The pinned version is 1.18.3, with the archive URL and checksum recorded in the [Microsoft WinGet manifest](https://github.com/microsoft/winget-pkgs/blob/master/manifests/h/hpjansson/Chafa/1.18.3/hpjansson.Chafa.installer.yaml). Other platforms require Chafa to be installed using the OS package manager or supplied with `--chafa-command`. A broken custom Chafa command is reported rather than replaced.

Prepare dependencies without opening setup menus or scanning music:

```powershell
python album_art_downloader.py --setup-dependencies
```

| Option | Effect |
|---|---|
| `--bootstrap` / `--no-bootstrap` | Automatic dependency installation is enabled by default. Disable installation while still allowing reuse of a working private environment. |
| `--bootstrap-dir PATH` | Choose a writable private runtime directory. |
| `--setup-dependencies` | Check/install dependencies, report readiness, and exit. |
| `--setup-dependencies --no-review-images` | Prepare Python dependencies without requiring Chafa. |

`--help` and `--version` work without third-party packages and never install anything. Internal tests require Python packages but do not require Chafa. Dry runs do not install Chafa. Disabling bootstrap does not disable ordinary MusicBrainz/image requests; it only prevents dependency installation. With `--no-bootstrap`, missing optional `send2trash` causes staging files to be retained.

Setup errors identify the missing dependency and a recovery action. Failed or interrupted installations are retained; rerunning uses a working environment or creates a new one. No failed installation is permanently deleted. Once dependencies are available, subsequent launches reuse them without downloading them again.

![Workflow](aad_workflow.png)

## Quick start

The easiest invocation is simply:

```powershell
album_art_downloader.py
```

With no arguments, it opens an interactive setup with this root menu:

```text
1. Current folder
2. C:\new\music
3. C:\soulseek
4. Enter another path
```

Choice 1 (the current folder) is the default. When `--art-type` is omitted, Windows interactive mode shows a two-column checkbox menu that responds immediately to each keypress. Toggle entries in place; press `S` to save the selection as defaults beside the script, or `Q`/Esc to finish without saving. It then asks whether to scan folders that already have artwork, whether to use dry-run, whether to review downloads visually, and finally asks for confirmation before doing any work. The artwork-scope question has no default when it is not supplied on the command line, so answer `y` or `n` explicitly.

Preview a run without writing artwork:

```powershell
python album_art_downloader.py --root C:\new\music --dry-run
```

Download every available artwork type for eligible folders:

```powershell
python album_art_downloader.py --root C:\new\music
```

Only inspect folders that contain no image files:

```powershell
python album_art_downloader.py --root C:\soulseek --missing-only
```

Download only front and physical-media images:

```powershell
python album_art_downloader.py --root C:\new\music `
  --art-type front --art-type cd --art-type vinyl --art-type cassette
```

## Default behavior

- Scans recursively.
- Skips folders beneath `Chiptunes`.
- Skips `ARCHIVAL-VERSIONS-NOT-FOR-PLAY` folders.
- Treats a contiguous numbered sequence beginning with track 1 as an album.
- Two numbered tracks are sufficient to identify an album.
- Writes album front artwork as `cover.*`.
- Writes physical-medium artwork as `cd.*`, `vinyl.*`, or `cassette.*`.
- Writes same-stem sidecars for non-album/MISC tracks.
- Downloads front, back, CD, vinyl, cassette, booklet, inlay, lyrics-art, and untyped release images.
- Preserves every existing image and skips filename collisions.
- Verifies downloaded image data before writing it.
- Uses year tags while searching when available.
- Writes a timestamped human-readable log.

![Album and MISC behavior](aad_album_vs_misc.png)

## Album detection

Auto detection recognizes common numbered track styles:

```text
01 Song.flac
1. Song.flac
1 - Song.flac
Artist - Album - 01 - Song.flac
```

The sequence must begin at 1 and be contiguous. Change this with:

| Flag | Effect |
|---|---|
| `--album-mode auto` | Detect numbered albums; this is the default. |
| `--album-mode always` | Treat every audio folder as an album. |
| `--album-mode never` | Treat every audio folder as MISC/non-album. |
| `--album-min-tracks N` | Change the minimum numbered-track count. |
| `--allow-numbering-gaps` | Accept sequences such as 1, 2, 4. |

## MISC behavior

`--misc-mode sidecar` writes one same-stem image per audio file. Existing same-stem artwork is preserved. Other choices are:

| Flag | Effect |
|---|---|
| `--misc-mode cover` | Write one `cover.*` for the folder. |
| `--misc-mode skip` | Do not write art in non-album folders. |
| `--misc-image-policy front-first` | Prefer a front image; default. |
| `--misc-image-policy first` | Use the source's first image. |

## Physical media

Cover Art Archive often labels physical media as `Disc` or `Medium`. The downloader inspects the type and comment:

- Generic disc or medium becomes `cd.*`.
- A vinyl or LP label becomes `vinyl.*`.
- A cassette or tape label becomes `cassette.*`.

![Physical-media names](aad_physical_media.png)

Change those names with `--cd-name`, `--vinyl-name`, and `--cassette-name`. `--disc-name` remains an alias for `--cd-name`.

## Artwork selection

When omitted, the downloader searches all available image types, including untyped images. Repeat `--art-type` to build an allow-list instead. Supported values are `front`, `back`, `cd`, `disc` (alias for CD), `vinyl`, `cassette`, `booklet`, `inlay`, `lyrics`, and `other`.

| Flag | Effect |
|---|---|
| `--art-type TYPE` | Download only selected types; repeatable. |
| `--include-untyped` / `--no-include-untyped` | Include or reject images without source labels. |
| `--max-images N` | Limit images per release; 0 is unlimited. |
| `--front-name NAME` | Change `cover` to another front-art stem. |
| `--back-name NAME` | Change the back-art stem. |
| `--booklet-name NAME` | Change the booklet stem. |
| `--inlay-name NAME` | Change the inlay stem. |
| `--lyrics-art-name NAME` | Change the lyrics-page image stem. |
| `--other-name NAME` | Change the untyped-art stem. |
| `--image-extension source|jpg|png` | Detect the source format from the bytes, or actually convert the image to JPEG/PNG. |

The `lyrics` artwork type means a photographed or scanned lyrics page. This tool does not download textual `.txt`, `.lrc`, `.srt`, or karaoke files.

In interactive mode, artwork types appear in two columns with `[✅]` and `[❌]` markers. Numeric keys are assigned first; if more entries are ever added, lowercase letters, punctuation, and uppercase letters are assigned next. `S` writes the current selection to `album_art_downloader.cfg` next to the script, and later interactive runs load that selection as the starting point. Command-line `--art-type` values suppress this prompt.

The menu contains the downloader's normalized categories, not every Cover Art Archive source label. For example, `medium`, `disc`, and physical-media comments are classified into `cd`, `vinyl`, or `cassette`; `front` is saved as `cover`. This keeps naming and collision behavior predictable while still searching all supported source labels by default.

## Existing files and collisions

The default `--collision skip` never overwrites an image. It recognizes an existing stem regardless of image extension, so `cover.png` prevents a second `cover.jpg`.

`--collision number` preserves both by producing names such as `cover (1).jpg`. This mode is available for investigation but is not recommended for routine collection cleanup.

## Missing-only modes

`--missing-only` can use three definitions:

| Definition | Folder is selected when... |
|---|---|
| `any-image` | It contains no image sidecar at all. |
| `front` | It lacks `cover`, `front`, and `folder` art. |
| `track-sidecar` | At least one audio file lacks a same-stem image. |

Missing-only reduces the number of folders modified. It does **not** decide whether existing artwork is good, clean, correctly matched, or high quality. Use a full scan plus Chafa review when you want to make those judgments yourself.

Example:

```powershell
python album_art_downloader.py --root C:\new\music `
  --missing-only --missing-definition front
```

## Tree controls

| Flag | Effect |
|---|---|
| `--recursive` / `--no-recursive` | Enable or disable recursion. `/s` is accepted as a shorthand for `--recursive`. |
| `--include-archival` | Include do-not-play archival folders. |
| `--include-chiptunes` | Include Chiptunes. |
| `--skip-part NAME` | Exclude a path component; repeatable and case-insensitive. |
| `--audio-ext EXT` | Recognize another audio extension; repeatable. |
| `--limit N` | Process at most N folders. |
| `--resume-after PATH` | Continue after a root-relative folder checkpoint. |

## Matching and network controls

| Flag | Effect |
|---|---|
| `--use-year` / `--no-use-year` | Include or omit the tagged year from release searches. |
| `--query-limit N` | Number of MusicBrainz release candidates requested. |
| `--search-strategy smart|exhaustive` | Stop unnecessary fallback/detail requests on strong matches (default smart), or perform the full search. |
| `--release URL_OR_ID` | Use a specific MusicBrainz release directly. Point `--root` at that release's folder. |
| `--rank-details N` | Fetch track listings for the top N preliminary matches (default 5; 0 disables these lookups). |
| `--network-retries N` | Retry temporary network failures up to N times (default 3). |
| `--choose-release` | Show release candidates, including `m` for a new manual artist/album/year search. When there are no candidates, offer manual search instead of silently ending the folder. |
| `--request-timeout SECONDS` | Metadata request timeout. |
| `--download-timeout SECONDS` | Image download timeout. |
| `--rate-limit SECONDS` | Minimum spacing between actual uncached MusicBrainz requests, including fallback queries and later folders. Cached queries do not consume the delay. |
| `--user-agent TEXT` | Override the HTTP User-Agent. |

## Validation

| Flag | Effect |
|---|---|
| `--verify-images` / `--no-verify-images` | Decode and verify downloaded image data. |
| `--min-bytes N` | Reject suspiciously small responses. |
| `--min-width N` | Require a minimum image width. |
| `--min-height N` | Require a minimum image height. |
| `--max-image-mb N` | Limit each downloaded or converted image to N MiB (default 32). |
| `--max-image-pixels N` | Limit decoded dimensions to N pixels (default 40,000,000). |
| `--deduplicate` / `--no-deduplicate` | Skip repeated source URLs and identical image bytes (enabled by default). Intentional same-image track sidecars remain supported. |

## Slow visual review with Chafa

Image review is enabled by default. Use `--review-images` (or `--verify-every-image`) to display every candidate image in the terminal before it is written; use `--no-review-images` to disable it. This uses Chafa through the same terminal-image preview workflow as `echo-image.bat`:

```powershell
album_art_downloader.py --root C:\new\music --review-images
```

Downloads are staged on disk, and Chafa receives each preview's bytes directly. When replacing an existing image, it shows the existing and proposed images in sequence, with dimensions, format, and byte size. The second preview does not clear the first. Use `--no-compare-existing` to show only the proposal. For each candidate you see:

```text
Keep image? [Y/n/o=open source/skip-album/retry/stop]:
```

- `Y` or Enter: approve the image for writing after the release is settled.
- `N`: reject the image; no sidecar is written for that candidate.
- `o`: open that image's source URL in your browser, then return to the same review prompt.
- `skip-album`: abandon the current folder and discard approvals from this release.
- `retry`: try the next MusicBrainz release and discard approvals from this release. If smart search shortened the list, exhausting it triggers the remaining searches first. If there is still no next candidate, the folder is reported as skipped without writing those images.
- `stop` or `S`: keep the current image, then stop asking for the rest of the run.

The review controls are `--chafa-command`, `--chafa-size`, `--chafa-format`, and `--chafa-clear` / `--no-chafa-clear`.

## Logging and audit

| Flag | Effect |
|---|---|
| `--log PATH` | Choose the timestamped text log path. Without this option, logs go to `C:\logs\album_art_downloader\`. |
| `--manifest PATH` | Append machine-readable JSON Lines results. |
| `--append-log` | Append instead of replacing the text log. |
| `--ansi-logging=yes` / `--ansi-logging=no` | Cycle verbose console lines through a rainbow ANSI palette (`yes` by default); startup and summary headers are colorful and emoji-based. The text log file remains plain text. |
| `--dry-run` | Search and plan without downloading files. |
| `--fail-fast` | Stop at the first folder error. |
| `--quiet` | Suppress console output while retaining the log. |

Logs end with a summary containing targets, matches, downloads, unmatched folders, errors, and skips. Console messages also include scan scope, selected artwork types, and filter counts; disable ANSI color for redirected or ANSI-unaware terminals with `--ansi-logging=no`. Replacing an existing log or report creates a verified sibling backup first.

## Matching, cache, and reports

Matching tries progressively broader MusicBrainz searches as needed in smart mode, or all fallbacks in exhaustive mode: tagged artist/title/year, artist/title without year, a relaxed title, and finally title-only. Use `--search-artist`, `--search-album`, and `--search-year` to override imperfect tags for a run. Candidates are ranked by artist and album similarity, year, track count, and track-title similarity when available. Track titles come from audio tags with filenames as a fallback. Each candidate displays its score and the contributing evidence; unavailable track listings are stated explicitly. These scores are heuristics, not probabilities. Track listings are retrieved through the [MusicBrainz release API](https://musicbrainz.org/doc/MusicBrainz_API).

Interactive runs present candidate releases for selection; `--choose-release` enables that behavior with an explicit root. Choose `l` to paste a MusicBrainz release URL or UUID, or use `--release URL_OR_ID` on the command line. The manual-search artist prompt also accepts a release URL/ID.

Temporary connection failures and HTTP 429/500/502/503/504 responses are retried with exponential delays. A server's `Retry-After` value, including an HTTP date, takes precedence. Log messages identify MusicBrainz, Cover Art Archive, or the image host. Interrupted image transfers restart from the beginning; incomplete staging files remain recoverable. Permanent failures are reported without repeated retries.

Responses are cached under `C:\logs\album_art_downloader\cache` for seven days by default. Use `--no-cache` to bypass it or `--cache-ttl-hours N` to change freshness. `--report PATH` writes an end-of-run JSON report by default, or CSV when the path ends in `.csv` (or with `--report-format csv`). Reports include both folder-level outcomes and individual image outcomes (`downloaded`, `rejected`, `skipped`, `discarded`, `retry`, or `would_download`) with art type, source URL, and target path.

Progress lines identify the current folder and its position in the scan. When a MusicBrainz search returns no releases in interactive matching, you can enter a new artist, album, and year or skip the folder. Approved images stay staged on disk until that release's review finishes, so retrying discards those approvals before another release is considered.

## Replacing existing art after review

The default remains non-destructive: existing targets are skipped. `--overwrite-after-review` permits replacement only after that particular image passes validation and visual review; it refuses to run with `--no-review-images`. If you choose `stop`, subsequent unreviewed images cannot replace existing files. Before every replacement, the script creates and verifies a sibling timestamped backup using the normal ChatGPT replacement-backup naming convention.

Image writes first flush a complete temporary sibling file, then rename it into place. An interrupted write leaves the original artwork intact and retains the temporary file for recovery. A target changed after approval is skipped. Existing filenames keep their suffix, and replacement bytes are converted to that suffix's format. New files use the detected format or the requested JPEG/PNG conversion. JPEG conversion flattens transparency onto white; conversions use the first frame of animated images.

## Automatic resume and disk staging (v37)

Resume is enabled by default. An append-only journal under `C:\logs\album_art_downloader\state` saves selected releases, staged-download hashes, keep/reject decisions, individual completed writes, and completed folders. It checks the scan settings and file metadata before reusing completed work; visual approvals also check image contents and existing target contents. Interrupted final journal records are ignored. Changed audio, artwork, or relevant options cause work to be reconsidered.

`--no-resume` starts a fresh assessment without loading or recording checkpoints. Use it when you want to search a completed folder again for newly available artwork. `--state-file PATH` chooses a journal location. Dry runs do not save completion or review checkpoints.

Staging defaults to `C:\logs\album_art_downloader\staging`, with a total 1,024 MiB disk budget and a 32 MiB limit per image. Set `--staging-dir`, `--max-staging-mb`, or `--max-image-mb` to change these. Downloads are streamed and checked against both limits; only the current image is loaded for validation/conversion/review. Approved albums do not accumulate image bytes in memory.

After a folder finishes, staging files are sent to the OS Recycle Bin using the optional `send2trash` package. `--keep-staging` retains them. If recycling is unavailable or fails, files are retained and the log explains why; there is no fallback to permanent deletion. Interrupted transfers and failed runs also retain their staging files. These retained files count toward the disk budget; recycle unneeded files or raise the budget when it fills. Recycled staging files remain recoverable from the Recycle Bin.

## Resume example

```powershell
python album_art_downloader.py --root C:\new\music `
  --log C:\logs\album-art.log `
  --resume-after "Cats Millionaire\Girls Rituals"
```

The checkpoint is compared case-insensitively against root-relative folder paths.

## Internal unit tests

The regression tests are built into the main program and do not require a separate test file:

```powershell
python album_art_downloader.py --unit-tests
```

The tests use temporary folders and mocked network responses. They do not alter the real music trees. Use `--version` to print the current script version.

## Source limitations

- Results depend on accurate Artist, Album, and Year tags.
- MusicBrainz may return no release or a temporarily unavailable service response.
- Cover Art Archive does not label every physical-medium image precisely; generic discs default to CD.
- Duplicate detection uses identical file bytes, not perceptual similarity; differently compressed copies may still be reviewed separately.
- The downloader does not embed artwork into audio tags. It creates sidecar image files.
