# PAFPlayer documentation

Current release: **V768** — push playback changes from the master through a client phone tree; clients cache full track and lyric payloads and advance lock-screen clocks locally without recurring status polls.
[Release notes](../releases/PAFPlayer_v768_event_driven_phone_tree_release_notes.md).

## Unique PAFPlayer features

PAFPlayer accepts live `#` commands during playback: press `#`, type a command, and
press Enter. `#commands` points to the complete command list. For example,
`#backwards` or `#backward` plays the current track backward; either command
toggles back to forward playback when already reversed. `#forward` always selects
forward playback. The reversed audio is prepared losslessly with FFmpeg and cached
under `runtime\cache\reversed-audio`; karaoke follows the reversed source-time
position and the progress bar fills from the opposite side. The `Ctrl+Alt+B`
shortcut remains assigned to its existing visualizer action.

A paused `--simple` preview also takes audio focus when resumed from the keyboard,
pausing other registered PAFPlayer instances immediately before its audio resumes.

[Full `#` command list](PAFPlayer_hash_commands.md).

## Console granularity safety

Shift+F4 requests a visualizer granularity change only while the console has input.
The prompt identifies the key or menu sequence that triggered it: press Y and then C
to confirm, or press N or Escape to cancel. It expires after 30 seconds. Favorites,
defaults, reset, and undo routes that would change granularity use the same protection.
Playback continues while the confirmation is displayed. Web settings remain separate.
Closing the playlist editor shows a notice for about 30 seconds.

## Inline lyric preview

Use `PAFPlayer.py --simple --use_lrc FILE AUDIO`, `--use_srt FILE AUDIO`, or
`--use_txt FILE AUDIO` to preview a supplied lyric file without changing the
audio file's sidecars. The option selects the parser, so the filename may have
any extension. A trailing `.maybe` is ignored only when checking the apparent
extension; it remains part of the filename loaded (`hello.lrc.maybe` is opened
literally). If the file cannot be verified, or its apparent extension is
unexpected, PAFPlayer warns and waits for a key, then continues and attempts
the preview anyway. The override is
authoritative for the first dispatched audio item only; later playlist tracks
return to normal lyric lookup.

`--simple` is intended for inline console use. It preserves the existing
console history, does not clear the screen, does not replace the console title,
does not render the startup title splash or normal PAFPlayer playback title/header, and disables the
heavier art, web, now-playing, and visualizer surfaces.
It also bypasses the loose-script self-install screen, so launching a loose
copy with `--simple` does not print an installer title or clear the console.
Batch launchers may set `PAFPLAYER_SIMPLE=1` when command-line expansion could
consume `--simple`; this has the same inline behavior.
Simple mode also forcibly disables PAFPlayer artwork and every visualizer
surface, regardless of saved artwork/visualizer settings, including the
pre-play opening-art render.
The normal `PAFplayer V… • filename` playback HUD title/control line is also
hidden in simple mode.

## Private Python runtime

Start an installed copy with `pafplayer.bat`. It uses the PAFPlayer-owned
`runtime\python.exe` when present, so changes to packages in your personal
Python do not change PAFPlayer. The core runtime is built with
`python -B tools/build_private_runtime.py`; exact core dependency versions are
in `requirements-core.txt`, including the Last.fm HTTP client dependencies. Build it before first-run installation to have the
self-installer copy it into the new installation under `C:\util\PAFPlayer`.
The runtime is a full app-local Python distribution with packages in a private
`site-packages` directory, not a virtual environment. Qwen/Piper model runtimes
and large model weights remain independently managed optional components.

The **AI DJ** tab groups related options into three cards. Its conversation
prompt, preset selector, editor, new-preset field, and save action occupy
predictable vertical rows and remain inside the configuration viewport.

## Lock-screen clock updates

Each client downloads the current track, lyric timeline, and timestamped playback anchor into its own memory. Its local lock-screen publisher advances the counter and selects timed lyrics from that cached payload. The master pushes a small event when the track/artist or transport anchor changes; one root client relays it through a binary phone tree, and each client fetches the full payload once for that event. There are no recurring status polls. The Windows lock-screen publisher reads only the local client endpoint, so second-by-second display updates stay on that computer.

## Remote playback update API

Tray clients register a callback with `POST /api/remote-tray/register` using the active player identity, a random client ID, an ephemeral callback port, and a random callback token. The master validates the registration against the active instance and limits callback destinations to private LAN addresses. A `topology` callback assigns up to two child clients; playback-change events go only to the root and are relayed down that tree. On a change, every client fetches `/api/remote-tray/hello?timeline=1` once to receive the full track, timestamp anchor, and lyric timeline. Clients unregister on shutdown; a failed branch is removed and the tree is rebalanced when the next event reaches it. The callback registry survives a master restart so online clients can be re-anchored by a pushed topology update. No client heartbeat or periodic master polling is used.

## Lock screen on a tray-only computer

The tray-only client enables lock-screen status by default. On startup, it checks Windows compatibility, the installed companion, and the certificate; if the companion needs installation or repair, it starts the existing bundled installer automatically. This check also runs when the music computer is temporarily disconnected. An earlier explicit choice to turn lock-screen status off is respected.

On the computer whose lock screen you want to update:

1. Start the main PAFPlayer on the music computer and leave it running with its web server reachable. Start `python PAFPlayer.py --tray-only MUSIC-COMPUTER:666` on this computer, replacing `MUSIC-COMPUTER` with the name or address shown by your player. You can omit the address to search the local network.
2. When the setup window appears, follow its instructions. If Windows asks an administrator to approve trusting the bundled **PAFPlayerLocal** certificate, approve the Windows prompt to continue. If the correct companion and certificate are already installed, PAFPlayer verifies them and does not reinstall.
3. Click **Open Windows settings** in the setup window. Under **Choose one app to show detailed status**, choose **PAFPlayer Lock Screen V530**. If your Windows settings also offer quick status, choose the same app there for the playing/paused icon. Return to the setup window and click **I selected PAFPlayer in Windows**. Windows controls this selection; PAFPlayer does not claim it can verify the selected slot.
4. Leave the tray connected. Click **Test lock screen** or press **Windows+L**. Unlock with your normal PIN or password. Windows controls how quickly and where status appears; a successful installation alone does not prove it is visible.

The existing V530 companion requires **64-bit Windows 10 build 19041 or later**. Windows 11 is now allowed to attempt installation, but its lock-screen display has not yet been verified; Windows may not offer the same status selection or show the companion’s text. If Windows reports User Account Control is disabled, open Start and search for **Change User Account Control settings**, move the slider above **Never notify**, click OK, restart Windows, and start the tray again. If installation fails or Windows approval is declined, the setup window explains the failure and offers **Install or repair** to retry. It also opens if the publisher cannot start. To reopen it later, find the PAFPlayer icon near the Windows clock (click the small up arrow if hidden), right-click it, and choose **Lock screen setup on this computer…**.

If the remote player disconnects, the local bridge stops supplying its previous song and resumes when the verified player reconnects. The setting is local to this computer and remote server; it does not change the music computer. If a full PAFPlayer is also running on this same computer, enable lock-screen publication in only one of the two clients.

Remote tray clients receive playback-change callbacks instead of polling the master. The master sends each change to one root client; registered clients relay the small event through a binary phone tree. Each client then fetches the full current-track payload, including the timestamped lyric timeline, and advances its own lock-screen clock and lyrics locally. The master sends no per-second or periodic status requests to clients. Track, artist, pause/stop, speed, and seek changes trigger a fresh payload. The decorative elapsed-time counter is rounded down to five-second steps before it reaches the V530 Windows companion, while lyric timing remains full resolution.

## HUD messages and warning history

Ordinary HUD messages remain visible for twice their previous requested
duration. HUD warnings remain visible until the current song changes. Warning
conditions that remain active are eligible to reappear every tenth song, but
only when the condition is still reported. Press **Shift+W** for a compact
screen of active track warnings, persistent HUD warnings, and unresolved
runtime warning summaries. The lowercase **w** key is no longer assigned to
the SIXEL visualizer. Esc or Q closes the warning screen.

## Web layout and controls

The web page keeps the song title in a neutral translucent backdrop so it does
not compete with the page-background artwork. The filename, status bubbles, and
URLs share a wrapping header row. Song links hide the `http(s)://www.` prefix in
their displayed label while retaining the full clickable destination. On narrow
or portrait layouts, links wrap inside a bounded column and status bubbles span
the row below. Web Emojimaxx substitutions use the device emoji font first, so
Apple devices display Apple Color Emoji while Windows keeps the player font
fallback. The web visualizer switch is directly above Web Karaoke, and the
Web Karaoke tab opens that combined area.

The configuration panel is disabled by default to leave more room for karaoke.
Use the gear button in the bottom-right corner to enable or disable it; the
choice is remembered in that browser. With Web Karaoke auto-expand enabled,
the lyric dock now remeasures the finished grid layout and fills the space
released when configuration is hidden.

The Console Visualizer row-height slider uses a wide track for finer control.
While it is being dragged, stale status responses cannot move its thumb. A
manual row-height adjustment turns off **Auto-set to tallest** so the automatic
mode cannot immediately replace the chosen height.

The Windows / Lock Screen, Steam, Last.fm, MonkeyMote, Monitoring, and Global
Config tabs use explicit ordering. Steam's reduction option is real pacing
control: when a detected Steam game is running, the console visualizer target
FPS is multiplied by 0.5 at its scheduling points. It does not change audio or
lyric timing.

Run `PAFPlayer.py --tray-only` without a server address to search the local
private LAN. The discovery probes the web port 666 and MonkeyMote port 19371,
then offers verified PAFPlayer web servers for selection.

Set tray-only startup features on another computer with flags, for example:
`PAFPlayer.py --tray-only music-pc:666 --floating-lyrics --floating-lyrics-always-on-top --art-lyrics`.
See [Windows tray controls](windows-tray.md#tray-only-clients-on-other-windows-computers) for all options.

In **Idle Behavior**, **Beat arc width** is a numeric spinner controlling the
total horizontal travel of **Speed bump — beat arc**. It defaults to 100 px;
the wider idle movement range remains available to the other wander patterns.


The web player displays the song title over a rainbow backdrop. The **Title backdrop transparency** control adjusts the whole title box.

## Emojimax text files

Run `pafplayer --emojimax "C:\path\file.txt"` to create `file - Emojimax.txt` beside a UTF-8 or BOM-marked UTF-16 text file. The original is preserved; existing output names receive a numbered suffix. Line endings and surrounding whitespace are retained. `--emojimax-file` requires a file, while `--emojimax "a phrase"` continues to preview a phrase.

## Experimental remote mouse

Start the player on Windows with `pafplayer --remote-mouse`. The host console prints a new eight-digit pairing code for that run. On a device connected to the same network, open the player web page, enable its configuration panel, and choose **🖱️ Remote mouse** at the bottom. Enter the code in the new tab; its touchpad moves the host pointer and its buttons perform left and right clicks. The feature is off without the command-line option, and the code changes each run. Use it only on a trusted network: the web connection is HTTP, so its pairing code and mouse commands are not encrypted. The page does not display the host screen or support click-and-drag.

## DJ conversation comparison

The comparison displays artist and song names in different colors, the complete active DJ instructions and cast settings, and model headings at double height in supported terminals. Run `pafplayer --ollamainstructions` to inspect detected Ollama models, or append a model name for model-specific connection steps. The command only reports instructions; it does not download or change models.

Run `PAFPlayer.py --ollamainstructions [model-name]` for staged local diagnostics. It checks Windows process presence, API reachability, visible models, the expected model-store path, and manifests on disk, then gives next steps for the detected state. For example, if the API responds but lists no models while manifests exist, it directs you to check the active server’s `OLLAMA_MODELS` path and permissions before restarting.

Run `PAFPlayer.py --ai` for a read-only AI DJ setup evaluation. It checks configured provider keys without displaying them, Piper voice files, model storage, and local Ollama availability. It can run an optional live text comparison using only free providers (never the paid OpenAI model) and open the voice/text model manager. `--dj-test` compares actual text generations.

Run `PAFPlayer.py --dj-test playlist.m3u` (or `--djtest`) to sample random visits using the configured DJ interval, lyrics, prompt, and cast, then compare available free hosted and installed local Ollama text models. Without a playlist argument it reads the running player's playlist. A running player using an older version must have its web interface enabled, or be restarted to provide the authenticated snapshot. Hosted models receive the selected track data and lyrics. `--include-paid` additionally tests the configured OpenAI model and may use API credits. The command does not play audio or change the running playlist. Local models are optional. Ollama may be running and reachable while its API lists zero models; check the active server’s `OLLAMA_MODELS` location and permissions, and restart only after correcting its model-store setting. To install GPT-OSS locally, run `pafplayer --models`, choose **Text models**, then **Download local GPT-OSS 120B** (about 65 GB); install and start Ollama first.

## Playlist window

Right-click one playlist track and choose **Edit tags…** (or press `Alt+3`) to open its tag editor. The editor previews embedded album art and can replace it from an image file. Before changing tags or artwork, PAFPlayer creates and verifies a sibling backup of the complete audio file.


Window opens, close requests and callback failures are recorded in the player trace log to help diagnose an unexpected disappearance.

With a playlist active, press **Alt+P** or **Ctrl+Alt+P** in the player to open or close the compact playlist window. Either shortcut also closes it while the playlist window has focus. Closing it shows “Playlist view closed” in the HUD for about 30 seconds. The list follows the active playback order; a fixed-width `>` marker and highlighted text mark the current track. Selecting a row does not play it. Use the arrow keys to select and scroll, and press Enter or double-click to play. Artist and title tags load in the background as `Artist - Title`, falling back to the filename; durations also load in the background and `--:--` means unavailable. Press **J** inside the playlist window to search the active list by filename, path, or loaded artist/title tags. Type multiple words to narrow the results, then press Enter or double-click a result to play it; Escape closes the search.

Shift-click selects a range; Ctrl-click adds or removes individual rows. Selections survive background metadata updates and current-track changes. Drag a selected row or group to move it within the active playback order. Play, tag editing, and Remove currently require exactly one selected track. As with console-browser reordering, this changes the live session order and does not rewrite the playlist file; another change to the playlist during a drag causes the move to be rejected rather than applied to the wrong track. Use **ADD FILE** or **ADD DIR**, or drop audio files and folders from Explorer onto the list. Folders are searched recursively. Existing PAFPlayer supported-format and duplicate rules apply; additions use its existing play-next behavior. Select a row and press Delete or **REMOVE**. Choose Yes to save the removal, No to keep it for this session only, or Cancel to leave it alone. The existing playlist undo behavior remains available in the player.

The window is inspired by the classic Winamp playlist editor, but it is a native PAFPlayer window rather than a Winamp skin: it does not reproduce skin bitmaps or every Winamp menu. Durations depend on optional Mutagen support and readable audio metadata. The classic editor's other controls remain available through PAFPlayer's console and web interfaces.

## Console command entry

During playback or pause, type `#` to show an editable command prompt in the console. The typed characters appear as you enter them; press Enter or wait 1.5 seconds to execute a nonempty command and dismiss the prompt. Backspace edits, Escape cancels, and an empty prompt simply disappears after 1.5 seconds. Holding Shift keeps the prompt open; the idle timer resumes after release. `#dj` toggles the AI DJ; `#djforce` requests commentary now. Ctrl+Alt+D retains album-art download / DRCS.

## Playlist errors

Missing playlist songs are skipped quietly, including consecutive missing entries; their paths and outcomes appear in the web configuration’s **Errors** tab. The list is newest-first and limited to the current player session. The error badge opens that tab. Other playback errors retain their configured alert delivery.

## Local voice model setup and comparison

Run `python PAFPlayer.py --models` (also `--model`, `--install-models`, or `--dj`) to open a separate window, including while another player is running. Choose Piper, Kokoro 82M, Qwen3-TTS 0.6B and/or Qwen3-TTS 1.7B, then use the buttons at the top to download the selected models or compare installed models. Initial interactive installation offers this as a skippable separate step. Downloads and their Python dependencies can require several GB. Models use isolated environments under `%LOCALAPPDATA%\PAFPlayer\support\voice-models`; existing Piper installations are reused. The comparison creates matching speech samples, per-sample generation timings and `results.json` in a new comparison folder, then opens that folder for listening. No model is downloaded without selecting it and clicking Download. The window displays live installer output, a current-step bar, overall model progress, and elapsed time. Direct model downloads show bytes, speed and a percentage when the server supplies a size; other stages use an animated bar rather than an invented percentage. The comparison does not automatically switch the DJ speech provider; PAFPlayer's DJ currently supports Piper and OpenAI speech. Qwen can use CUDA if its installed PyTorch supports it; otherwise CPU generation may be slow. Voice quality and speed should be judged on the actual machine.

## AI Podcaster / DJ

When AI DJ is enabled, the player prepares free Piper voices in the background at startup if needed. The AI DJ tab shows detected automatic executable and voice paths, missing configured paths, setup progress and a **Download / repair free Piper voices** retry button only when setup is missing or incomplete. The button is hidden when an automatic install or valid configured local voice setup is already available. **Talk Now!** queues the same forced commentary request as console `#djforce`. **Wake now** and **Sleep now** are session overrides matching `#djwake` and `#djsleep`; sleep cancels pending/current DJ commentary, and the saved schedule is unchanged. Blank paths mean automatic setup. Missing configured paths are skipped in favor of working paths or the automatic install; existing choices are preserved. Downloads use disk space and network bandwidth.

The console `#` prompt accepts named commands in addition to `#dj` and `#djforce`. `#djwake`/`#wakedj` wake the DJs for the session; `#djsleep`, `#sleepdj`, `#sleeping`, `#bed`, `#bedtime`, `#sleepy`, and `#sleep` put them to sleep. `#help` opens the normal key overlay, while `#commands` or the shorter `#?` gives a command-list reminder; the complete command table is in [PAFPlayer_hash_commands.md](PAFPlayer_hash_commands.md). `#volume` enters the same direct volume editor as the `V` key. `#quit` exits immediately; transport, shuffle/repeat, speed, playlist, warning, URL, visualizer, karaoke, artwork, and lyric-window aliases are also available.


The AI DJ tab exposes the editable dialogue prompt. Select an example to inject it; Restore previous / current prompt returns to the text from before choosing a preset. Save prompt settings to persist your selection, and use Save as new prompt to add a named preset. Random picks from current, previous, built-in and saved prompt texts for each conversation. The placeholders `{speakers}`, `{seconds}`, `{women}`, and `{men}` are replaced from the DJ settings. Track history contains artists and titles, not lyrics. The DJ marks newly played tracks separately and includes up to three recent DJ conversations to discourage repetition; this context is sent to whichever text provider is selected. Recent DJ dialogue is kept in memory for the current player session. The political example has no live news feed and asks the model not to invent current events. Custom prompts must request the expected JSON format. A visible fixed instruction asks speakers not to introduce themselves or use numbered speaker labels.

The AI DJ tab includes **AI DJs go to sleep**, defaulting to **never**. Pick an hourly sleep time to reveal a wake selector, which defaults to **sunrise**, or select a fixed hourly wake time. Sunrise reveals a US ZIP field: confirm or change the default **22312** for your location during setup. Sunrise uses approximate local solar calculations; ZIP 22312 works offline. Other US ZIP codes are sent to Zippopotam.us for approximate coordinates, which are cached locally. If the ZIP lookup or sunrise is unavailable (including polar day/night), 7:00 AM is used and a warning is shown. Times use the player computer’s local time zone.

**AI DJs go to sleep when screen is locked** is available both in the DJ controls and under Windows Lock Screen; the two checkboxes immediately save and reflect the same setting. When asleep, automatic DJ jobs do not start, prepared automatic segments wait, and active automatic speech stops. `#djforce` overrides both scheduled and screen-lock sleep for that request. Music resumes if the DJ owned its pause. Unlocking or the scheduled wake time allows the next eligible segment to play.


The **Conversation model precedence** section has five ordered dropdowns: OpenAI text, OpenRouter GPT-OSS 120B (free), OpenRouter free router, Gemini (free tier only), and local Ollama. The default uses that order. Move providers between priorities or set entries to **Off**; choosing a provider already in another slot swaps their positions. PAFPlayer tries each selected provider in order and advances after a failure. OpenAI may use API credits. Gemini runs only when its free-tier confirmation is enabled. Supply `OPENROUTER_API_KEY` and `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) through `C:\BAT\private.env` or the player environment; keys are never displayed in settings or written to DJ logs. Artist/title metadata goes to whichever hosted text provider is used, and provider data policies vary. Piper remains the local speech fallback.

If OpenAI returns the specific `credit_balance_exhausted` error, Help and the bottom **Warnings** web tab show the last confirmed observation. The warning persists across restarts for the same key and clears after a successful OpenAI text request. It does not claim a balance for an untested key, or treat an ordinary rate limit as exhausted credit.


DJ dialogue and recent artist/title metadata are appended to `C:\logs\PAFPlayer\dj.log` when text is generated, including when voice synthesis later fails or the prepared speech is not played. Entries show local date and time, most recent song first, and gender-marked speaker turns. This log contains listening history and dialogue. A write failure is shown in Help and Warnings; playback continues. In contrast, DJ diagnostics are saved as separate append-only JSONL files under `%LOCALAPPDATA%\PAFPlayer\workflows\dj-logs`. Each session records scheduling decisions, provider stages and failure types, HTTP status codes, cancellation, and playback outcomes. It does not record track metadata, generated dialogue, API keys, error bodies, or provider response text. The `?` screen shows the number of qualifying tracks while waiting, and shows progress for automatic as well as forced requests. When Help is open, prepared commentary waits until Help closes before it claims the music pause. Resuming a manual pause preserves a ready automatic segment. Help warns if the DJ diagnostic log could not be opened.

During playback, `#dj` toggles automatic commentary; `#djforce` requests it now after at least three seconds of the current track. Open `?` or F1 to see DJ status and generated dialogue below the track diagnostics and above the shortcut list. The text appears as soon as it is written, even if voice synthesis fails. Long dialogue uses Help's PgUp/PgDn pages. Help updates while open, including when playback is paused. A failed request retains the last successfully generated text; the status identifies the current failure.


The feature is off by default. Open the web configurator’s **AI DJ** tab to enable it and configure recent-track history (default 10), frequency (2 qualifying tracks), approximate length (90 seconds), and speaker counts (one woman and one man by default; previously saved choices are preserved). Changing either gender count balances the other; increasing the total adds women unless you change the counts. Gender is a requested cast, not a guaranteed characteristic of the provider’s voices. Piper uses configured voice models when provided; otherwise it automatically installs its default voices, including a second voice for the default cast. If the second voice cannot be downloaded, it falls back to one voice and reports a warning.

PAFPlayer prepares a conversation on a background worker from the artist and title of tracks actually heard. It asks the provider to focus on newly played tracks and a fresh angle; near-identical recent scripts are rejected and another provider may be tried. It prefetches from the history available at preparation time, so a prepared segment may not include a track completed while it was being generated. Automatic commentary waits for a track boundary: if it becomes ready during a song, it plays at the beginning of the next eligible track. `#djforce` is an immediate interruption. It pauses music for commentary and resumes only a pause it owns. Pausing, stopping, seeking, or changing tracks cancels the active interruption. A forced request while music is already paused leaves it paused. A forced request needs a played track: the current track becomes eligible after at least three seconds of playback. A forced request joins an existing job; its HUD message reports stages rather than a percentage. Automatic retries stop after a provider failure until settings change or a new force request is made.

OpenAI Responses supplies text and OpenAI Realtime supplies speech by default, using a valid `OPENAI_API_KEY` from `C:\BAT\private.env` when present, otherwise from the player’s environment. The private-file key takes precedence so a stale inherited environment value does not override it. Artist and title information are sent to OpenAI when cloud providers are selected; voice audio is AI-generated. Requests may incur API charges. The key is not entered into or displayed by the web settings. OpenAI speech requires the optional `websocket-client` Python package in the player’s interpreter. The documented Realtime voice presets are selectable in order; they are distinct when enough presets are provided. Accent is an instruction, not a guaranteed voice characteristic.

The configured order determines whether Ollama is tried after hosted text fails. If selected without a model name, PAFPlayer chooses the smallest model in Ollama’s visible catalog. Local model loading and generation can take minutes; the background request allows up to ten minutes. Ollama supplies text only. If cloud speech fails, the DJ automatically sets up Piper and a default local voice when needed. Setup downloads Piper and dependencies plus the 63.2 MB voice model into the configured **Model storage folder** under `Piper`. It runs in the background and verifies a real speech file before marking the install ready. Existing configured executable and voice paths are retained. Piper model order controls speaker voices; models repeat when fewer are supplied than speakers. The web section shows whether the executable and configured voice model files are found; detection does not prove they work.

You can still follow the [Piper installation and voice-download guide](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md) and provide executable and ONNX paths in the web settings. Model licences and accents vary; consult the chosen model’s card. An automatically installed default voice is reused for speakers without configured local voices. A running Ollama server with at least one downloaded model is separately required for local text. Setup failures appear in Help without stopping the music; retry with `#djforce` after correcting the cause. Incomplete setup folders are retained and are not reused.

Generated commentary WAVs are retained in uniquely named `PAFPlayer commentary` folders under the system temporary directory; they are not silently deleted. Speech currently uses FFplay’s default output device, which can differ from the configured music output. Provider and synthesis failures are shown without stopping music. On the test machine, a local Ollama model generated dialogue in about 79 seconds after an earlier request timed out; a subsequent test using automatic model selection took 110 seconds. The newer OpenAI service key authenticated, but an OpenAI text request returned HTTP 429 `credit_balance_exhausted`; OpenAI speech remains unverified. Live free-tier OpenRouter and Gemini dialogue plus Piper speech passed with synthetic track metadata. A live local Ollama-to-Piper test generated six speech files in about 54 seconds, and a muted FFplay check succeeded.

## Start and configure

- [What PAFPlayer is](../PAFPlayer.md)
- [Single-file installation, folder layout, and readiness checks](distribution-layout.md)
- [First-install survey rehearsal](install-survey.md)
- [Private FFmpeg setup](ffmpeg-setup.md)
- [Web configuration](web-config-playback.md)

## Playback and display

- [Playback controls and global shortcuts](playback-controls.md)
- [Playlist editing, Delete/undo, resume, and shuffle](playlist-controls.md)
- [Ways to queue files and folders; music library search](music-library-and-enqueue.md#ways-to-queue-files-in-the-active-playlist)
- [Artwork window controls, karaoke sizing, and shortcuts](window-shortcuts.md#v645-resize-cursors-and-focus-only-maximize)
- [Floating Lyrics](floating-lyrics.md)
- [Web visualizer, karaoke, and progress bar](#web-visualizer-karaoke-and-progress-bar)
- [Console rendering](console-rendering-v482.md)
- [Large-playlist transitions](large-playlist-transitions.md)

## Windows and household integrations

- [Windows tray and remote tray-only controls](windows-tray.md)
- [Native tag viewer and tray popup](windows-tray.md#native-tag-viewer)
- [Windows lock-screen status and media panel](windows-lock-screen.md)
- [Visual screensaver](visual-screensaver.md)
- [Discord profile integration](discord-integration.md)
- [MonkeyMote remote control](monkeymote.md)
- [Remote-control API](remote-control-api.md)
- [Remote Floating Lyrics](remote-floating-lyrics-v574.md)
- [Steam-aware visualizer and artwork](steam.md)
- [Last.fm configuration](web-config-playback.md#v572-lastfm-tab)

## History and diagnostics

- [Current V645 release notes](../releases/PAFPlayer_v645_artwork_window_controls_release_notes.md)
- [Complete release history](PAFPlayer_changelog.md)
- [Open work](PAFPlayer_TODO.md)
- [Performance measurements](performance-v519.md)
- [V580 remote tray verification](PAFPlayer_v580_remote_tray_and_steam_manual.md)

Historical versioned manuals, measurements, and release artifacts remain in
`docs/` and `releases/`. Some older releases never had standalone notes; their
feature history is recorded in the changelog.

## Web visualizer, karaoke, and progress bar

The web visualizer has a **Web visualizer** checkbox in its toolbar. Turning it
off hides the canvas and stops its frames while leaving the player controls and
configuration available. Double-clicking the canvas toggles the same saved
setting. Opening the page only reads artwork-coloring and autoslide settings;
it sends changes to PAFPlayer when you change a control.

### Lyric size and panel height

**Auto-Expand Lyric Size** fits each current lyric to the web lyric panel.
Short lines grow, and long or wrapped lines shrink. Drag the handle below the
lyric panel to give it more or less height. The saved manual height takes
priority when you drag it smaller, and the font is refitted as the panel
changes size. The fitter checks rendered characters as well as the element's
scroll dimensions, so large glyphs stay inside the panel even when they
extend beyond their CSS line boxes. Long words can wrap. This web setting
does not change console or floating lyric font sizes.

### Seeking and lyric titles

Clicking the web progress bar moves its displayed position immediately. The
display reconciles with the player once the seek takes effect; audible seek
time can still vary with decoder startup or a busy player loop. Hovering over
the bar previews the lyric at that position. If there is no current lyric, a
recent line appears half faded for up to five seconds.

Timed lyrics stop occupying the console and taskbar title after the existing
15-second maximum, including when the next cue is much later or a sidecar
provides a long end time. The browser lyric title timeline uses the same
cutoff.

### Web configuration controls

The **Experimental** section includes **Idle artwork dance timeout** and
**Window-dance range**. The timeout is the number of seconds without Windows
keyboard or mouse input before artwork starts its idle dance; `0` disables
automatic activation. The range is a percentage of the artwork window's
current monitor, from `0%` (stationary) through `50%`. Changes are saved for
later runs, apply to the current artwork window immediately, and remain
clamped inside one monitor.

Enable **Dance to music** beneath those controls to drive both the main artwork
and related-art gallery windows from the same timestamped beat pulse used by
progress-bar coloration. Quiet passages pause movement; stronger pulses move
the windows farther per animation frame. The selected progress-bar beat
detector and timing correction remain the single analysis source—this option
does not run another FFT or decoder. Dance range and monitor-edge protection
still apply. The checkbox is off by default while the behavior is experimental.

When a missing, empty, or unreadable track reaches the same error-delivery path
used by the Wilhelm scream, a **⚠** badge appears beside the web song title.
Its tooltip says **Click for errors**. Clicking it opens a newest-first,
auto-refreshing error page containing the filename, reason, recovery outcome,
path, and time. The list is bounded to 250 entries, exists only in memory, and
is cleared when that PAFPlayer process exits.

The **Console Visualizer** section has a **Maximum console visualizer FPS**
number field. Enter a whole number from 1 through 120 and leave the field or
press Enter to save it. The factory setting is **60 FPS**. The console renderer
uses this as a ceiling immediately and remembers it for later runs; its
adaptive frame governor or Steam game load reduction may run it slower. This
field does not set the browser visualizer's frame rate or change audio timing.

The **Silence / overlap between tracks** control has an editable seconds box
beside its slider. Enter a value from -5 to +5 seconds. Positive values add
silence. Negative values are saved as overlap requests, but the current
renderer does not yet mix adjacent tracks. The configuration tabs follow the
page's section order as you scroll.

**Beat visual timing correction** has an editable millisecond box beside its
slider. The slider snaps to `0` within ±15 ms; the box accepts whole values
from -250 through +500 ms. Its factory value is `0 ms`. Beat energy uses the
same timestamp source as lyrics, the spectrum, and progress. Live spectrum
data is a fallback until the matching timestamped analyzer sample arrives.

The visualizer header has no extra “Live spectrum” caption. The output status
chip uses **Out:** for sample rate, bit depth, and optional source bitrate.

The AI DJ sends available local lyrics and track metadata to the selected text provider. Its prompt forbids invented personal experiences. Model comparison displays progress and playable samples in its window. `--install-wav-context-menu` adds a per-user WAV queue action.

During DJ commentary, available speech text appears in karaoke. Pause, play, seek, and previous/next operate on the DJ audio while it is active; the underlying song remains paused. Spectrum analysis uses the DJ audio. Conditions that remain active are reminded after ten songs.

During DJ commentary the external artwork window displays a collage of the discussed tracks’ available primary artwork; missing covers receive placeholders. Song artwork is restored afterward.

Run `PAFPlayer.py --models` and choose **Text models…** to compare free hosted GPT-OSS 120B and other text providers using the same editable prompt and example track data. The optional Ollama download is approximately 65 GB and needs substantial memory; it runs only when selected. To use that local model for the DJ, select Ollama in AI DJ configuration and set the Ollama model to `gpt-oss:120b`. Auto mode tries free hosted GPT-OSS before the free router, then the remaining configured providers. Free hosted availability can change. Gemini may charge unless project billing is disabled.

The model manager opens in a separate process and returns to the command prompt, where progress messages continue. The text-model window sizes itself for display scaling and shows local GPT-OSS download percentage, transfer rate, and ETA without terminal control codes.

`--no-ai` or `--noai` disables AI DJ generation and model setup for the process without changing saved settings. Piper synthesis uses a detached, hidden process. DJ conversations are instructed not to announce an unknown upcoming song. The DJ visualizer uses its own speech clock. Auto-mode console artwork remains available while paused unless competing playback is detected. Ctrl+O is available in the playlist window. A bare playlist supplied to an existing instance asks whether to replace or queue; `--playlist` replaces, `--queue` / `--enqueue` / `--en` queue next, and `--queue-at-end` / `--enqueue-at-end` queue at the end.

AI DJ settings save automatically; Load / save DJ profiles manages only DJ settings, with Factory Defaults and Developer’s Choice when the DCC contains DJ settings. Saving DJ settings to DCC is available on the designated developer computer. Ctrl+mousewheel changes the playlist window font size.

In the playlist window, right-click the column header to choose number, song, length, last played, year, album, folder, or genre. Right-click one selected track or press Alt+3 to edit its tags. Editing creates and verifies a uniquely named sibling backup before writing metadata. Ctrl+mousewheel changes playlist font size.

AI DJ settings include a **Model storage folder** field. The existing stores are already on `T:\\models`: PAFPlayer voice models and Ollama use verified junctions there. If you choose a different folder, use the `--models` window’s **Move models** action so files are copied, verified, and re-linked before future use.

The `--models` window can move model storage to a chosen empty directory, defaulting to `T:\models` when T: exists. It copies and verifies files before switching original paths to Windows junctions. Original directories are retained as sibling backups, so their space is not automatically reclaimed. Ollama uses a shared `Ollama` store under the destination; Piper uses `Piper`, and other voice model folders are at the destination root. Do not start downloads or model operations during the move.

A previously relocated unified model store can be moved again to a new empty destination; shared Piper and Ollama directories are copied only once. The model window reports byte progress.

## Tag-editor runtime support

Mutagen 1.47.0 is a required package in `requirements-core.txt` and is included in
`runtime/Lib/site-packages/`. The runtime builder verifies its import before
publishing a build; readiness checks report it as required. Select one song and
press Alt+3 or right-click → Edit tags. This works offline and downloads nothing
when opening the editor. Use the launcher to select the bundled runtime. An
incomplete or different Python runtime gets an actionable error; an existing
completed V746 cache can still be loaded offline for compatibility.

## Download storage and legacy helper cleanup

Automatic application-support downloads now live under `PAFPlayer/runtime/`:
Claire helpers in `runtime/clairecjs_utils/`, FFmpeg in `runtime/support/ffmpeg/`,
lock-screen installation payloads in `runtime/downloads/LockScreenInstaller/`,
and model downloads by default in `runtime/models/`. A model directory explicitly
chosen in configuration and explicit media Save As destinations retain that
choice. Existing FFmpeg and metadata caches remain readable for compatibility;
new support files are never downloaded beside `PAFPlayer.py`. The runtime builder
keeps its Python installer cache inside the staged runtime as well.

At startup PAFPlayer moves root `claire_*.py` files into
`runtime/clairecjs_utils/`. If a name already exists, both copies are preserved;
the legacy copy goes under `runtime/clairecjs_utils/legacy/` with numbered
collision suffixes as needed. The runtime helper folder is in the import lookup.

## Native lock-screen publisher V531

V748 bundles and requires the signed V531 companion. Earlier Python clock fixes
could still use V530, which resubmitted an unchanged badge with every timer tick.
V531 sends changing text tiles every second and renews the badge only when its
glyph changes or its 30-second lease needs renewal. A badge update is always
followed by a text tile so detailed status stays populated. The tray bridge uses
cached timestamped lyrics during a transient network timeout for up to 15 seconds;
it expires that lease and rejects different player owners. It does not request
lyrics from the master per timer tick.

Restart or reload the updated tray on each client. Its existing setup flow detects
V530 and upgrades the signed package to V531 using the same certificate. Accept
an existing Windows install prompt if one appears. When choosing the detailed
status app in Windows, select PAFPlayer Lock Screen V531. Native tests verify
one-second submissions; Windows still controls when the physical lock screen
paints, which must be observed on the locked client.

## Inline interruption and startup status

Ctrl+C and Ctrl+Break in `--simple` (or `--light`) stop playback without homing or
clearing the screen, resetting the cursor color, or replacing the inline display
with a full-screen reset. The cursor and current text rendition are restored for
the shell. Simple-mode interruption unwinds through cleanup.

Startup status rows share a colon column directly after the web-server port
label (for example `666:`). MonkeyMote and playlist-resume rows use that same
column. Resume output has three rows: Resuming playlist, Resuming song, and
Resuming at. Only the playlist and song filenames are italicized.

## Global pause keys and simple previews

While another PAFPlayer is running in the same Windows session, `--simple` and
`--light` previews ignore Win+C, Pause/Break and Media Play/Pause. This includes
older players, explicit instances and tray-only clients using PAFPlayer.py.
If the preview is the only player, it can respond to those keys. The process
check runs when the key is pressed, so starting or stopping another player during
a preview changes the decision on the next press. Space in the focused preview
remains available. Other playback instances keep their existing hotkey behavior.

## Speed multiplier entry

Press X, type any positive finite multiplier and press Enter: `x1.37` then Enter
sets exactly 1.37×, and `x0.75` sets 0.75×. Values are not restricted to the web
selector's presets or rounded to them. Decimal and scientific notation and an
optional `x`/`×` suffix are accepted. Zero, negative values, NaN and infinity are
rejected. Backspace edits, `=` resets to 1× and Esc cancels.

Custom speed follows playback, pause/resume, seeking and subsequent tracks in the
same session. A fresh process starts at 1×. Selecting a dropdown preset replaces
the custom multiplier; speed-up/down keys move to the next preset in that direction.
X no longer stops playback; Ctrl+W, Ctrl+C and Alt+F4 remain available for stopping.

## Seeking and local HTTP diagnostics

Seeking may close the decoder's previous RAM-audio HTTP connection. Disconnects
during request parsing, header writes, streaming or final flushing no longer
print socketserver tracebacks over the inline console. Expected disconnects go
to `trace.log` as `memory-audio.client-disconnected`; unexpected request failures
keep their traceback in the PAFPlayer error log. Seeking and byte-range reads
continue normally after a failed request.

## Normal-height output after playback

When playback completes, is stopped or is interrupted, subsequent stdout/stderr
text and console output reset each row with `BIG_OFF` (`ESC # 5`). This includes
wrapped completion status, blank lines, errors, cleanup messages and the next
prompt row. The guard remains active until another track starts; active karaoke
can then use double-height lines again. Simple mode keeps its existing screen
content and does not clear the screen to reset row sizes.


### V755: preview audio focus and console space

`--simple` pauses the main player and other simple previews immediately before starting its first decoder. A local authenticated loopback listener coordinates players even when their web servers are disabled. Closing a preview releases its pause requests; players that were already paused stay paused. Nested previews resume the preceding preview first and keep the main player paused until all preview requests have ended. Crash recovery expires abandoned requests after approximately 12 seconds. Restart running players once to enable this coordination. The console visualizer now reserves one bottom safety row instead of two.


### V756: exact speed confirmation and minor credit warnings

The X menu labels the active speed as Playing and the typed value as Pending until Enter. Applying or resetting a speed clears the menu and redraws the HUD with the actual custom multiplier, including while paused. The decoder retains the precise multiplier.

Past OpenAI credit exhaustion stays in Web Warnings and DJ diagnostics as a minor issue. It appears in the HUD/help warning list only when DJs are enabled, OpenAI participates in the configured text/speech chain, and the latest generation has failed without a ready fallback result. This decision uses cached job state and makes no network requests on the playback thread.


### V757: idle artwork frame pacing

The idle artwork dance targets 60 frames per second using monotonic deadlines. Callback work no longer adds a full delay to every frame, and missed frames are skipped rather than replayed in bursts. Position-only dance Configure events reuse the existing artwork instead of resampling the image and scheduling border/title updates. Monitor geometry comes from the existing display watcher. Motion speed and monitor-safe bounds remain time based.

Every ten seconds while dancing, diagnostic tracing records `art.idle.pacing`: actual FPS, longest callback gap, longest callback duration, and extra-window count. These measurements help distinguish UI stalls from compositor/display issues. Restart the player to load this change; real visual smoothness still needs comparison on the affected display.


### V758: simple-preview startup recovery

`--simple` checks registered peer process liveness before connecting, archives registrations for exited processes under `workflows/playback-peers/retired/`, and traces focus startup, skipped dead peers, pause acknowledgements and readiness. This prevents accumulated crash leftovers from adding seconds of refused connections per old preview. A fresh preview starts unpaused and does not overwrite the main player's saved pause setting.

The newest preview takes priority over older preview startups. Older previews acknowledge their silent pre-decoder state and wait for the newer preview to finish, rather than both startup threads waiting for pause commands neither can consume. Existing pause leases continue to preserve the main player's original state.


### V759: preserve paused/stopped players during previews

A player that was already paused or stopped stays that way when a simple preview starts and exits. Preview-owned transport is resolved on the audio thread against current leases, so a pending restore cannot restart a player after another preview has taken over. Explicit Pause/Stop revokes preview restore ownership. Automatic external-media resume and stale Play commands are held while a preview lease is active. Diagnostic events record lease ownership and approved/blocked restoration without authentication data.

Restart the main player once as well as previews to load the receiver-side guards. Only players that a preview actually paused are eligible for automatic restoration.


### V760: Ctrl+C cleanup below the stop message

After printing `Playback stopped.`, the Ctrl+C handler emits ANSI erase-to-end-of-screen (`ESC[J`) before its newline and flushes the output. This clears leftover karaoke/progress content below the message while preserving text above it and the existing simple-mode terminal behavior.


### V761: faster preview startup

Metadata and edge-silence analysis now survive process restarts in `runtime/cache/track-analysis`, keyed by the audio file identity, size, timestamps, analysis parameters and tool version. Unchanged preview files can reuse analysis while changes invalidate it. Failed scans are not persisted. Original files and trim/gain settings are unchanged.

Isolated audio workers reuse compiled player code under `runtime/cache/worker-code`, keyed by source contents and Python bytecode version. Workers retain the real script path, isolated process and normal command/status protocol. Missing/unreadable caches fall back to source startup. Entries are immutable; no existing cache files are replaced or deleted. Cold first-use analysis still takes time.


### V764: keep one visible gap after circled lyric numbers

Windows Terminal receives one safety cell after each contiguous run of ❶–❿ substitutions. Double-height rendering consumes that compatibility cell, while the lyric's own separator remains visible as one gap. A run such as ❶❽ is padded only after its final digit. The separate pen-glyph workaround remains.


### V762: pause peers only when preview audio is ready

Simple previews register for coordination during setup but leave the other players playing. The buffered audio renderer loads and primes silently first; only then does the preview acquire pause acknowledgements and release its prepared output. If preparation fails, the fallback pauses peers immediately before launching FFplay. Failed silent preparation never acquires focus. Existing focus ownership and previously paused-player protections remain in effect.
