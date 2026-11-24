# PAFPlayer V746 — tag-editor dependency repair

The playlist editor previously imported Mutagen directly. Alt+3 and the context-menu tag action failed with “No module named mutagen” in a runtime missing that optional package.

Opening either action now prepares Mutagen on a worker thread, displays elapsed setup status, and opens the original selected song after setup. It downloads the pure-Python Mutagen 1.47.0 wheel over HTTPS from PyPI, checks the published SHA-256 digest, rejects escaping archive paths, and stores a completed package in the application's autodownloaded folder. A read-only installation falls back to the user's local application cache. No pip, administrator rights, or global Python change is required. Metadata workers discover cached packages without initiating downloads. A failed setup reports a retry and manual-install command.

Validation covers existing packages, verified installation, cache reuse, hash rejection and path traversal rejection. Audio tag round-trip verification uses a generated fixture, not library files.
