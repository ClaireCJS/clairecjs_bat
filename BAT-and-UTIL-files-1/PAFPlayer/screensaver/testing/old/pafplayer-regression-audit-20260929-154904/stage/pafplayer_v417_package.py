"""Write release notes, docs, immutable snapshot, and deployment manifest."""
from pathlib import Path
import hashlib
import json
from pafplayer_v416_edit import ROOT, replace_file, unique


notes = '''# PAFPlayer V417 — Winamp URL controls and audio downloads

September 21, 2026. Build `2026-09-21-v417-wawi-controls-and-downloads`.

V417 includes the V416 TODO, synchronized timeline, circled-digit spacing, and external-media pause/fade work. The detailed qualifications and validation for those changes remain in [V416 release notes](play_audio_file_v416_release_notes.md).

## Existing Winamp BAT URLs

PAFPlayer now accepts these paths on its own HTTP host and actual bound port. Both GET and HEAD execute a command once; HEAD compatibility matters because the existing scripts use `wget32 --spider`.

| URL | Behavior |
| --- | --- |
| `/play` | Play/resume; already-playing audio stays playing. |
| `/pause` | Toggle pause/resume, matching WAWI and `winamp-unpause.bat`. |
| `/unpause` | Explicit play/resume alias. |
| `/stop` | Stop audio and reset to the playable beginning; keep PAFPlayer and its web server available for Play. |
| `/next` | Existing next-file action. |
| `/prev`, `/previous` | Existing previous-file action. |
| `/main` | WAWI-compatible state phrases understood by `winamp-status-from-file.pl` and the BAT fast parser. |
| `/winamp?page=main` | Alternate legacy status URL. |

The web player's square Stop button now has the same reset-and-wait behavior. Console quit and the older API `stop` command retain their exit behavior. Explicit Stop cancels ownership of an external-media automatic pause, so another player finishing cannot unexpectedly resume a manually stopped track. Pause/resume holds the current position; Stop resets it.

To direct the existing BAT controls to PAFPlayer, use its startup banner's host/port for `TMPMUSICSERVER`, and the same address plus `/main` for `MUSICSERVERSTATUSURL`. For example, when PAF binds port 666 on this computer:

```bat
set TMPMUSICSERVER=127.0.0.1:666
set MUSICSERVERSTATUSURL=http://127.0.0.1:666/main
```

Use the actual advertised port if 666 is already occupied. This release does not rewrite the user's BAT files, environment, or WAWI credentials. Their existing prerequisite checks remain; `winamp-stop.bat` still intentionally skips its request when already paused unless invoked with `fast`. Playlist upload/clear and Girder key commands are separate interfaces, outside this transport compatibility addition.

## Filename and download behavior

- Filename/path click from the player computer opens the current track's folder in Explorer.
- Filename/path click from another computer downloads the current audio file.
- The small down-arrow button immediately to the right always downloads, on either computer.
- Both links support keyboard navigation and have descriptive tooltips; the download button has an accessible label and hides when no track is available.

Local/remote classification uses the TCP peer and the accepted socket's local address, including loopback, the computer's LAN address and IPv4-mapped IPv6. It does not trust the URL's Host header or forwarded-address headers. This is intended for direct connections to PAFPlayer, not a reverse proxy that hides client identity.

`GET /api/audio/download` streams the original current file in 128 KiB chunks, with its size, media type, and an attachment filename. Unicode names use the [RFC 6266 UTF-8 filename form](https://www.rfc-editor.org/rfc/rfc6266.html) plus an ASCII fallback. HEAD returns the same metadata without the body. The endpoint never accepts an arbitrary filesystem path. Each transfer holds one opened file, so advancing the playlist cannot splice a different song into the download. Missing files return a clear HTTP error; cancelling a download does not stop playback. Remote requests to open Explorer are rejected.

## Validation

- 13 new tests pass: real GET/HEAD control requests, the installed GNU Wget 1.5.2 `wget32.exe`, the actual Perl status parser, both stopped-player transitions, manual Stop versus automatic resume, exact download bytes, HEAD framing on a persistent connection, Unicode/header-safe filenames, current-file snapshots, local/remote authorization, and JavaScript link behavior.
- All 56 existing V416/V402/V401/V397/V394 focused tests pass in isolated module processes; six additional embedded web/transport checks pass.
- All embedded browser JavaScript parses with Node; browser inspection confirms the filename link and small adjacent download button render correctly.
- One combined process run aborted in native PortAudio device initialization. Isolated module runs pass; the new mocked player-loop test explicitly selects track-only visualization so it does not initialize unrelated microphones.
- A second physical client was not used. Remote behavior is covered by HTTP classification/authorization tests and executed JavaScript link tests.

'''

audit = json.loads((ROOT / 'pafplayer_v417_historical_audit.json').read_text())
notes += f"The historical suite ran {audit['run']} tests with {len(audit['failures'])} failures and {len(audit['errors'])} errors; the failure and error names exactly match the V416 baseline (45 failures, 5 errors), with no new names. It is not fully green. See `pafplayer_v417_historical_audit.json` and the V416 baseline for individual historical failures.\n"
replace_file(ROOT / 'play_audio_file_v417_release_notes.md', notes)

for relative in ('PAFPlayer_changelog.md', 'docs/PAFPlayer_changelog.md'):
    path = ROOT / relative
    prefix = '../' if relative.startswith('docs/') else ''
    entry = f'''## V417 — September 21, 2026

Added WAWI-compatible GET/HEAD transport URLs and legacy state output for the existing Winamp BAT scripts. Stop now resets and waits for Play without closing the web session. Filename clicks open Explorer locally and download remotely; a small adjacent download button always saves the original audio. See [release notes]({prefix}play_audio_file_v417_release_notes.md) for setup, exact semantics, and validation.

'''
    content = path.read_text(encoding='utf-8')
    replace_file(path, content.replace('## V416', entry + '## V416', 1))

path = ROOT / 'docs/play_audio_file.md'
content = path.read_text(encoding='utf-8').replace('Current release: **V416**.', 'Current release: **V417**. See the [V417 Winamp URL/download notes](../play_audio_file_v417_release_notes.md).')
content = content.replace('## Quick start', '''## Winamp BAT controls and downloads

The existing `/play`, `/pause`, `/stop`, `/next`, and `/prev` URLs accept GET and `wget32 --spider` HEAD requests. `/pause` toggles; `/main` exposes the state phrases consumed by the existing scripts. Point `TMPMUSICSERVER` and `MUSICSERVERSTATUSURL` at PAFPlayer's actual advertised host/port. Web Stop resets to the beginning and waits for Play while the server stays running.

Click the filename to open Explorer on the player computer or download the audio from another computer. The small down-arrow immediately beside it always downloads. Direct endpoint: `/api/audio/download`.

## Quick start''', 1)
replace_file(path, content)
path = ROOT / 'play_audio_file.md'
replace_file(path, path.read_text(encoding='utf-8').replace('[V416 release notes](play_audio_file_v416_release_notes.md)', '[V417 release notes](play_audio_file_v417_release_notes.md)', 1))

source = ROOT / 'play_audio_file.py'
data = source.read_bytes()
compile(data, str(source), 'exec')
snapshot = unique(ROOT / 'play_audio_file_v417_wawi_controls_and_downloads.py')
snapshot.write_bytes(data)
assert snapshot.read_bytes() == data
manifest = {'source': str(source), 'versioned_source': str(snapshot),
            'sha256': hashlib.sha256(data).hexdigest(),
            'installed_before_sha256': hashlib.sha256(Path(r'C:\BAT\play_audio_file.py').read_bytes()).hexdigest()}
replace_file(ROOT / 'pafplayer_v417_release_manifest.json', json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
