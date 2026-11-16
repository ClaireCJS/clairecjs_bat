# v163 — album art downloader fallback

The existing MusicBrainz/Cover Art Archive, Discogs, Bandcamp, and iTunes search remains first. If it fails without an explicit user rejection, `audit_music_batch.py` calls the supported `album_art_downloader.download_artwork_for_folder` API, then embeds its Front sidecar into the intended audio targets. A user-declined image never triggers the fallback. Tests with injected network fetchers continue to use only their specified sources.

Keep `audit_music_batch.py` and `album_art_downloader.py` importable together for this optional fallback; the audit tool retains its existing primary artwork workflow if the downloader is unavailable until a primary failure occurs.
