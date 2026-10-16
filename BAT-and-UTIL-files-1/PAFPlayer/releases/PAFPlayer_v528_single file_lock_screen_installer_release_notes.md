# PAFPlayer V528 release notes

Released October 12, 2026.

The single-file player now embeds the complete lock-screen installation payload:
the signed V528 x64 MSIX, pinned PAFPlayerLocal certificate, validated installer,
and runtime integration.

- `PAFPlayer.py --install-lockscreen` installs or upgrades the companion.
- `PAFPlayer.py --check-lockscreen` validates the embedded payload and reports the
  installed version without changing Windows.
- A normal first run attempts installation once per Windows user and release.
- On first run, an untrusted self-signed certificate goes directly to the required
  Windows UAC approval. The explicit command also asks for `y` confirmation first.
- Payloads are SHA-256 verified before Windows sees them and extracted into a
  versioned user cache without overwriting unexpected files.
