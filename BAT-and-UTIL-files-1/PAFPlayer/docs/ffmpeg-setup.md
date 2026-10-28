# Private FFmpeg setup (V577)

PAFPlayer uses FFplay for its legacy renderer and FFmpeg/FFprobe for decoding,
visualization, metadata, and speaker tests. If they are missing, obtain a
trusted Windows FFmpeg ZIP URL and its **expected SHA-256** from the same trusted
publisher or another independent verified channel. Then run:

```powershell
python PAFPlayer.py --setup-ffmpeg HTTPS-ZIP-URL EXPECTED-SHA256
```

PAFPlayer shows the source host, expected hash, and private destination and
waits for you to type `YES`. It downloads only after that approval. It hashes
the complete ZIP, rejects a mismatch or unsafe archive paths, extracts into
`%LOCALAPPDATA%\PAFPlayer\support\ffmpeg`, and checks that `ffmpeg.exe` and
`ffplay.exe` report versions. It then rescans the private location and reports
the exact installed version, path, and hash. Existing builds remain intact;
the newest valid private build is preferred without changing system PATH.

The installer does not supply a default ZIP URL or a guessed hash, because a
publisher can replace an archive at the same URL. If setup fails, install
FFmpeg/FFplay manually and place them on PATH, or retry with a verified ZIP and
its matching hash. Failed staging files are sent to the Recycle Bin; a recycling
failure leaves the staging folder in place and reports its path.
