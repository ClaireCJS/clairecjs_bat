# Clips4Sale preview downloader

The Clips4Sale preview downloader scrolls a studio/category listing to the end,
selects the best-quality edition of repeated titles, visits the selected clip
pages, and saves their public preview videos, animations, and still images.

## Installed location and launcher

The runnable copy is installed at:

```text
C:\BAT\clips4sale_downloader\
```

Launch it without adding anything to `PATH` using:

```text
C:\BAT\clips4sale_downloader.bat
```

The launcher passes the listing URL and every option through to the installed
application. It uses the bundled environment when present, then the configured
system Python fallback.

Both supported launch names use the same installed application and behavior.

## Login persistence

The default headed Chrome session uses a dedicated reusable profile at:

```text
the temporary application profile under `%TEMP%`.
```

Log in once in the Chrome window the downloader opens. Later runs reuse that
profile and its cookies, so they do not ask you to log in again. If another
downloader already owns the profile, the new run automatically clones the
login-bearing profile into an isolated sibling profile instead of failing with
Chrome's profile-lock error. The clone retains the same login cookies while
using its own lock, so concurrent runs do not require another login. Use
`--profile-dir "D:\somewhere"` to choose the preferred profile root.
Each run navigates the initial tab opened by its own browser context, so a
concurrent run gets its own visible browser instance rather than leaving a
startup `about:blank` tab in front. A small OS-backed launch lease prevents two
processes from racing to start the shared profile before Chrome creates its own
singleton lock; the second process goes directly to its isolated login clone.
The downloader also recognizes the legacy `lockfile` left by older releases,
so an older active instance cannot make a new run wait on the shared profile.
Browser startup is shown in the transient status row and has a 30-second
launch timeout with a readable error instead of an indefinite pause.
Concurrent profile copies include only login settings, cookies, and site
storage. Browser metrics/history databases and component caches are omitted.
The current filename and elapsed copy time appear in the status row and log.
SQLite snapshots have a 5-second deadline; the whole copy has a 30-second
budget. A locked login file produces a named error, with the incomplete copy
preserved for inspection, instead of waiting forever or using incomplete
cookies.
Chrome can also exclusively lock its cookie file while a retained window is
open. The downloader keeps completed idle login copies in
the temporary profile snapshots and falls back to one when that happens. These
copies retain Chrome's encrypted cookies; they do not export plaintext
passwords or cookie values. An older idle run profile can bootstrap the first
snapshot after upgrading. The source used is named in the log. Snapshots are
refreshed before launching an idle profile and after browser cleanup, before
the window is reopened. A snapshot reflects its saved login state; a new login
in another running browser will be available after that run finishes.
Even when a completed listing cache avoids re-scraping, the headed browser
still opens the requested listing URL. When a headed persistent run ends or is
cancelled, the downloader hands its profile back to a normal visible Chrome or
Edge window at the last page visited, so it does not disappear with
Playwright's cleanup. Use `--close-browser-on-exit` if that hand-off is not
wanted. Headless and `--no-persistent-login` runs cannot leave a logged-in
window open.
The test-only `--no-persistent-login` option creates an isolated session.
The downloader does not write your username or password to `%TEMP%`. The
profile stores the browser session/cookies using Chrome's normal per-user
storage, which avoids creating a plaintext password file. When a login page
redirects away from your requested listing, press Enter after completing it;
the downloader reopens the original URL automatically. A logged-in session
starts scanning without an Enter prompt, including concurrent instances.
Use `--pause-before-scrape` to explicitly stop for same-page overlays or other
manual browser setup before scrolling.

## Run on this computer

A project virtual environment is already set up. From this folder in PowerShell:

```powershell
C:\BAT\clips4sale_downloader.bat "https://www.clips4sale.com/studio/54509/latinass-locas/Cat183-cuckolding/Page1/recommended/Limit24"
```

1. Choose a destination by its number, or choose **Enter another location**.
   When `%USERNAME%` is `claire`, Enter selects
   `C:\new\p\clips4sale-previews` (and creates it after selection).
2. Chrome opens. Complete any site prompts, then press Enter in the terminal.
3. The program scrolls the whole listing, selects editions, then saves each clip's media.
4. Between clips it counts down the duration measured from the downloaded preview.

After the listing reaches a stable end, its complete clip list is stored in
`clips4sale.db`. Resume and failure-retry runs reuse that cached list instead
of scrolling the listing again. Use `--refresh-listing` when you explicitly
want a new scrape.

The menu offers the current folder and `C:\new\p\clips4sale_previews` **only if
that folder already exists**. It does not silently create or select the default.
Use `--output "D:\somewhere"` to add another choice. That choice is still subject
to the numbered prompt; a missing custom folder is created only after selection.
Choose `0` or press Ctrl+C to cancel.

## Installation in another environment

Requires Python 3.10+, Chrome (or Edge), FFmpeg's `ffprobe` on PATH, and Claire's
shared `clairecjs_utils.claire_progressbar` library. The library resides at
`C:\clairecjs_utils` and must be importable by your Python interpreter.

```powershell
py -3.10 -m venv --system-site-packages .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If using an existing environment, use its Python executable instead. For Edge,
pass `--browser msedge`. For Playwright's bundled Chromium, first run
`python -m playwright install chromium`, then pass `--browser chromium`.
Supply `--ffprobe "C:\path\to\ffprobe.exe"` if ffprobe is not on PATH.

The shared rainbow library is used directly. This project does not install or
replace copies of that library.

## Filenames and quality selection

The linked listing supplies this prefix:

```text
cuck - Jasmine Mendez LatinAss Locas - Cuckolding - <clip title>.mp4
cuck - Jasmine Mendez LatinAss Locas - Cuckolding - <clip title>-preview-gif.gif
cuck - Jasmine Mendez LatinAss Locas - Cuckolding - <clip title>-image.jpg
```

Only one primary preview, one GIF-family preview, and one best still are
downloaded. If both GIF and WebM versions of the same animation are exposed,
the GIF is selected. A thumbnail is considered as a candidate for the best
still and is not downloaded as a redundant second file.

`--studio-name` and `--category-name` override the prefix. Without a category
filter, each clip's own category is used. This is what makes a full-studio URL
such as `Cat0-AllCategories` produce the same studio/category/title structure
for every file instead of labeling every file `All Categories`.
Bare studio URLs without a `Cat...` segment and older cached listings with a
blank category behave the same way. The clip's explicit primary category wins;
otherwise its first listed category is used. Related categories never override
the site's primary `category_name`. Missing category data uses `Uncategorized`.

New videos also embed that category in their standard **Genre** metadata tag.
FFmpeg stream-copies the downloaded staging file without re-encoding its media,
and ffprobe verifies the tag before the final filename is published. The
untagged staging file goes to the Recycle Bin only after successful publication;
if recycling fails, it is retained with a warning (never permanently deleted).
Tagging failures preserve staging files and are reported, not marked complete.
Use `--ffmpeg PATH` if FFmpeg is not on `PATH`. Already-complete videos remain
untouched and are not downloaded again just to add a tag; GIF/JPEG sidecars
receive category-bearing filenames but are not remuxed as videos.

Optional sortable category abbreviations are disabled by default. Pass
`--category-prefixes` to add `sph -`, `cuck -`, or `ch -` where applicable;
without that option, filenames begin with the studio, category, and title.
Invalid Windows filename characters are replaced; overly long names are
shortened with the clip ID retained.

For a full-studio URL, the scanner keeps scrolling until the studio listing is
quiet at the bottom. It then uses each clip's own category for the filename,
for example `Holly Hardy - Small Penis Humiliation - <clip title>.mp4`.

Duplicates are matched within a studio using case-insensitive titles after
removing trailing edition labels such as `(HD)`, `- 4K`, `1080p`, and `MP4`.
Different parts retain their separate titles. Resolution/dimensions determine
quality, with advertised file size as a tie-breaker. Explicit resolution fields
take precedence over title labels; title labels are a fallback when resolution
is absent. The first listing wins ties. The report records discarded editions.
This is metadata-based selection; it does not compare video content visually.

All discovery finishes before selection, including when `--max-clips` is used,
so a higher-quality edition later in the listing can still win. The preview's
resolution can differ from the full product's advertised resolution.

## Waiting and progress

The bottom terminal row is the persistent shared Claire rainbow global-progress
taskbar for the whole run. The row above is the reusable current-operation bar:
each media transfer gets its own progress value, but the same line is overwritten
for the next transfer; during pacing it becomes the wait/countdown line. An
ANSI scrolling region keeps logs above the two locked rows, and long log lines
are clipped so they cannot wrap into the taskbars. The original console mode and
scroll region are restored on exit. Windows Terminal/ConPTY is treated as ANSI
capable even when classic console-mode probing is unavailable. Set
`C4SDL_NO_ANSI=1` only when output is being redirected to a non-terminal.
If a terminal wrapper reports stderr as redirected while stdout is interactive,
the renderer automatically uses stdout; `C4SDL_FORCE_ANSI=1` is available for
wrappers that report both streams as redirected.
Both progress rows use the full available console width through the shared
`clairecjs_utils.claire_progressbar` renderer (with one edge cell reserved to
prevent wrapping). Long filenames are shortened to leave room for the bar.
Console messages are colored by purpose: green for saved files, muted cyan for
already-complete skips, amber for waits/retries, red for errors, violet for clip
headings, and blue for other information. Text logfiles remain uncolored.
The renderer checks the live output-device dimensions every 0.2 seconds, even
while browser or network calls are waiting. Like PAFPlayer, it anchors its two
rows to the current viewport, clears the previous footprint, and rebuilds the
scrolling region on width or height changes. It never needs a new download to
notice a resize, and stops its resize watcher before restoring the terminal.
Use a normal terminal such as Windows Terminal.

After saving a clip's media, `ffprobe` measures its video durations. The longest
saved preview/animation duration determines the pause before the next clip.
There is no duration-based inter-clip pause after the last clip. The per-video
pause described below still applies immediately after a newly downloaded final
video. If a duration cannot be measured, the fallback is 30 seconds;
`--fallback-wait` changes it. Errors are reported. A clip whose saved media is
already complete has no inter-clip wait at all; a short 1.00–5.00 second
coordination wait is reserved for media still owned by another active run.
The advertised duration of the paid full-length clip is never used for pacing.

Newly downloaded video files receive an additional random 0.40–4.20 second
pause, rounded to hundredths. After every five newly downloaded videos there is
also a random 1.20–7.30 second pause. After a randomly selected interval of
17–27 newly downloaded videos there is a random 3.30–13.70 second pause; the
next interval is selected independently. A video already complete in the job
database adds no inter-clip wait. If media is still being handled by another
concurrent run, the measured duration pause is replaced by a random 1.00–5.00
second coordination wait. These pauses are recorded in the live status line
rather than creating extra terminal rows. Obsolete failed media rows do not
push a clip marked complete to the end of the queue.

Each job remembers its previous positive scheduled wait across scrolling,
page settling, download pauses, and inter-clip backoffs. Consecutive waits
cannot use the same duration at hundredth-second precision. If a random pause
repeats, another hundredth-second value is chosen within the original range.
Fixed/minimum delays round upward to hundredths; an exact repeat receives an
additional random 0.01–1.00 seconds, never a shorter wait. Zero-delay skips stay
instant and do not reset the history. Logs and JSON reports use the adjusted
inter-clip duration. Internal refresh/polling timers are not pacing delays and
are unchanged; independent concurrent jobs keep independent delay histories.

Ctrl+C immediately releases the terminal before browser cleanup: it stops the
resize watcher, restores the full scrolling region and cursor, erases the two
status rows, and advances past the bottom row. Cancellation/report text and the
next shell prompt then use normal scrolling instead of landing inside the bars.

A clip with a failed media item also uses a random 1.00–5.00 second backoff
instead of the 30-second unknown-duration fallback, so one missing CDN asset
cannot make the queue appear stuck. Every run writes a timestamped log under
`C:\logs\c4sdl`; failed media entries include the role, attempt number, HTTP
status/type, URL, and the reason for the following wait. The JSON report
records the failed role and URL, and interrupted runs are marked
`completed: false` with an explicit interruption reason and traceback. Pacing
delays do not call the browser driver, so a browser cleanup problem cannot
interrupt an otherwise resumable queue. The downloader restores Python's
normal Ctrl+C handling because the shared console helper otherwise converts
SIGINT into an ambiguous `SystemExit(0)`.

Discovery uses a 2-second minimum scroll delay (with the repeat adjustment
above). A listing finishes after eight quiet checks
at the bottom, with no pending site data requests and no visible loader. Adjust
`--scroll-delay` and `--stable-rounds` for a slow connection. `--max-scrolls`
provides an abort limit; reaching it fails instead of downloading a partial list.
Previously failed clips are moved to the end of the queue, allowing pending
clips to be completed first. A clip already marked complete with all saved files
present skips detail-page/media discovery entirely.

## Useful options

```powershell
# Discover everything, inspect only one selected clip, and write a plan without saving media:
C:\BAT\clips4sale_downloader.bat "<listing URL>" --dry-run --max-clips 1

# Save at most three selected clips after scanning the entire listing:
C:\BAT\clips4sale_downloader.bat "<listing URL>" --max-clips 3

# Headless is useful only when the site needs no interactive prompts:
C:\BAT\clips4sale_downloader.bat "<listing URL>" --headless

# Show the installed version:
C:\BAT\clips4sale_downloader.bat --version
```

`--help` lists all options. Headed Chrome is the default. Site gates require
manual interaction. HTTP authentication/rate-limit failures stop the run.
Extraction uses the site's exposed clip data and direct media files; HLS/DASH
manifests and DRM are not supported. If the site changes its data shape, the
program reports missing clip/media data rather than selecting unrelated media.

## Files, reports, and interrupted runs

Existing files are preserved. A collision produces `name (1).mp4`, then
`name (2).mp4`, and so forth, immediately before the final extension. Downloads
are streamed into exclusive `.part` files and published only when complete.
Failed/interrupted downloads retain their partial files.

The application keeps one SQLite job ledger in its private data directory. It records clip IDs,
media URLs, saved paths, attempts, and failures. A later run automatically
resumes: successful media is skipped, an interrupted/failed item is retried,
and a clip encountered through two categories is still stored once because the
ledger identity is the studio plus clip ID. SQLite claims also keep two
concurrent runs from downloading the same media twice.
Retries retain their original media reservation. On Windows, process ownership
is checked with a process handle, never `os.kill(pid, 0)` (which sends Ctrl+C
on Windows). Each failed attempt is saved before console output, so an
interrupted retry still goes to the end of the next run's queue. Abandoned
processing records from older releases also go to the end once their owner
process has exited.

Each run writes a new `clips4sale-run.json` or `clips4sale-plan.json` containing
selected clips, duplicate decisions, media URLs, saved paths, measured durations,
waits, and errors. Existing reports receive collision suffixes too.
Media claims are serialized in SQLite; a matching media URL is linked to its
existing saved path even if the site exposes it under another clip record, so
overlapping category runs do not create a second copy. Files already present at
their deterministic names are adopted into the ledger rather than renamed with
`(1)`.

Text logs are written to `C:\logs\c4sdl\`, with one collision-safe logfile per
run. The JSON report records the logfile path. The listing cache is stored in
the private database, so an aborted download can resume without re-scraping the
completed listing. If `C:\BAT\private` exists it is used; otherwise the ledger
and reports go under the user's AppData area. Browser profiles live under
`%TEMP%` and may be discarded safely; they are not part of the application
folder. An older destination-local ledger is imported automatically on its
first run after this change, preserving completed URLs and listing caches.

To rerun only failures from a report or database:

```powershell
C:\BAT\clips4sale_downloader.bat --retry-failures "<private report or database path>"
```

The listing URL and destination are read from the report when available; they
can still be supplied explicitly. Each failed media item gets one additional
attempt by default. Use `--media-retries N` to change that. Exit status is `0`
for success, `1` for failures, or `130` for cancellation. Missing media (HTTP
404/410) is recorded as a failure and receives the normal retry attempt by
default. Browser cleanup errors after a disconnected driver do not replace the
saved report.
After the retry is exhausted, a missing preview does not stop the other media
or the next clip. Logs show the start and result of each attempt; reports include
the downloader version, process ID, and individual attempt errors.

## Tests

```powershell
.\.venv\Scripts\python.exe -B -m unittest -v
```

The tests exercise synthetic scrolling with multiple batches, a better edition
in a later batch, scoped media extraction, folder selection, collisions, HTTP
failures, actual FFmpeg duration measurement, and a complete two-clip run. All
browser requests use fixtures; the only HTTP server is local. Unique test
artifact folders are retained, so running tests does not delete files.

Browser API reference: [Playwright Python network documentation](https://playwright.dev/python/docs/network).
