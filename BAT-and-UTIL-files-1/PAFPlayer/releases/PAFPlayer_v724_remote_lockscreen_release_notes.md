# PAFPlayer V724 — Tray-only lock-screen status

The tray-only menu now has a local lock-screen setup window with installation, Windows Settings, UAC recovery, and lock-test instructions. Installation occurs only when explicitly requested in that window. The existing V530 companion and its bundled, verified installer are reused; it supports x64 Windows 10 build 19041 or later, not Windows 11.

An opt-in local loopback bridge supplies the companion with current metadata, transport, and synchronized lyric state from the verified remote session. It returns an unavailable response while disconnected, renews its local lease when the remote player identity changes, and stops its publisher on tray exit. Settings are stored per tray endpoint. The existing companion remains responsible for Windows publication.

Tests cover the real loopback HTTP bridge, disconnect and owner changes, lyric timing, opt-in state, the Tk instructions window, the current V530 installer, and bundled source parity. Actual certificate installation and the visible Windows lock screen were not exercised. Two older V505 package tests cannot run because their V505 release artifact is absent from this checkout; V530 installer artifact checks passed.
