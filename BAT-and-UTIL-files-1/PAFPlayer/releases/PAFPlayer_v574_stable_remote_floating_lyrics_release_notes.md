# PAFPlayer V574 — Stable remote Floating Lyrics

Remote tray clients no longer restart the track intro every 50 milliseconds or
queue alternating visibility toggles. Real lyric cues cancel stale intro hide
timers, and saved enabled modes start correctly. Whip Emojimaxx keeps its
existing hieroglyphs and renders them using a supported font fallback.

The native two-process test also exposed Tk controls attached to the wrong
interpreter and a missing pointer-sized DestroyIcon binding; both are fixed.
V573 lyric character recovery, setting IDs and playback command ownership are
preserved. The existing HTTP port override is documented: `--web-port=PORT`
(default 666), with matching `--tray-only HOST:PORT` on clients.

Verification: **143 focused/related tests passed**, zero failures/errors/skips;
player and **21 embedded modules** compiled. Two real local player/client runs
recorded all **72 and 73** sampled lyric window states as visible, delivered
successive cues, and exited cleanly. Installed Windows glyph coverage and masks
verified the Whip fallback. A real remote-computer visual check remains pending;
these are not screenshots or proof of behavior on a different computer.

See [the full guide and evidence](../docs/remote-floating-lyrics-v574.md) for the
reproduction, manual procedure and limitations. Upgrade/reload the remote client
too.

The tested V574 source is preserved as `PAFPlayer_v574_stable_remote_floating_lyrics.py`. Another chat advanced
the working source to V575 before this release record was finalized. V575 retains
these fixes plus its volume-color change; this work did not roll it back.

Source SHA256: `325715bef38e48dba2b465edc6c1a0de11d60052453350526ab0a3eb931f0596`.

No literal C:\BAT paths were changed by this operation. No files were deleted.
Replacement backups were created and hash-verified before edits. The complete
path inventory is [here](../tests/reports/remote-v574-file-changes-20261018.json).
