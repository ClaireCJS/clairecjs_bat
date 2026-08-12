# album_art_downloader.py

`album_art_downloader.py` scans a music tree, identifies releases through MusicBrainz, retrieves their images from Cover Art Archive, and writes verified artwork sidecars. Its defaults encode the artwork workflow developed for `C:\new\music` and `C:\soulseek`.

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

Choice 2 is the default. It then asks whether to use missing-only mode, dry-run, Chafa verification, and finally asks for confirmation before doing any work.

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

Repeat `--art-type` to build an allow-list. Supported values are `front`, `back`, `cd`, `disc` (alias for CD), `vinyl`, `cassette`, `booklet`, `inlay`, `lyrics`, and `other`.

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
| `--image-extension source|jpg|png` | Choose the output extension. This does not transcode image bytes. |

The `lyrics` artwork type means a photographed or scanned lyrics page. This tool does not download textual `.txt`, `.lrc`, `.srt`, or karaoke files.

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
| `--recursive` / `--no-recursive` | Enable or disable recursion. |
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
| `--request-timeout SECONDS` | Metadata request timeout. |
| `--download-timeout SECONDS` | Image download timeout. |
| `--rate-limit SECONDS` | Delay between source requests. |
| `--user-agent TEXT` | Override the HTTP User-Agent. |

## Validation

| Flag | Effect |
|---|---|
| `--verify-images` / `--no-verify-images` | Decode and verify downloaded image data. |
| `--min-bytes N` | Reject suspiciously small responses. |
| `--min-width N` | Require a minimum image width. |
| `--min-height N` | Require a minimum image height. |

## Slow visual review with Chafa

Use `--review-images` (or `--verify-every-image`) to display every candidate image in the terminal before it is written:

```powershell
album_art_downloader.py --root C:\new\music --review-images
```

Chafa receives the image bytes directly; no temporary preview image file is created. For each candidate you see:

```text
Keep this image? [Y/n/stop]:
```

- `Y` or Enter: write the image.
- `N`: reject the image; no sidecar is written for that candidate.
- `stop` or `S`: keep the current image, then stop asking for the rest of the run.

The review controls are `--chafa-command`, `--chafa-size`, `--chafa-format`, and `--chafa-clear` / `--no-chafa-clear`.

## Logging and audit

| Flag | Effect |
|---|---|
| `--log PATH` | Choose the timestamped text log path. |
| `--manifest PATH` | Append machine-readable JSON Lines results. |
| `--append-log` | Append instead of replacing the text log. |
| `--dry-run` | Search and plan without downloading files. |
| `--fail-fast` | Stop at the first folder error. |
| `--quiet` | Suppress console output while retaining the log. |

Logs end with a summary containing targets, matches, downloads, unmatched folders, errors, and skips.

## Resume example

```powershell
python album_art_downloader.py --root C:\new\music `
  --log C:\logs\album-art.log `
  --resume-after "Cats Millionaire\Girls Rituals"
```

The checkpoint is compared case-insensitively against root-relative folder paths.

## Tests

Run the test suite from the project folder:

```powershell
python -m unittest discover -s tests -p "test_album_art_downloader.py" -v
```

The tests use temporary folders and mocked network responses. They do not alter the real music trees.

## Source limitations

- Results depend on accurate Artist, Album, and Year tags.
- MusicBrainz may return no release or a temporarily unavailable service response.
- Cover Art Archive does not label every physical-medium image precisely; generic discs default to CD.
- `--image-extension jpg|png` controls the filename suffix but does not transcode bytes. Prefer `source` unless another workflow requires a forced suffix.
- The downloader does not embed artwork into audio tags. It creates sidecar image files.
