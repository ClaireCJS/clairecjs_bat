# PAFPlayer V470 — persistent Discord and sleep bass controls

- Discord webhook setup now saves only to Windows Credential Manager for the current Windows account. It is restored on future player runs, never written to PAFPlayer configuration files, the registry, logs, or returned by the web UI. The Discord panel can forget it.
- Added Playback controls for reducing bass while Windows is locked and for an opt-in bass boost/reduction amount. The signed ±100% control maps to a bounded ±20 dB, 120 Hz low-shelf filter; the locked reduction uses the same scale.
- Config tabs now use a direct click handler and direct scroll assignment, avoiding the previously unreliable smooth-scroll/focus path.
- An unfocused album-art popup makes its wrapper chroma-transparent instead of drawing the gray focus border.
- All terminal abort signals use the fast shutdown route; the signal handler restores normal font mode, autowrap and cursor, then homes and erases the screen before other cleanup.

Known follow-up work remains for the requested expanded beat-treatment catalog and its before/after/inversion targeting controls. Those must be added together with renderer behavior and regression tests; merely adding checkboxes would be misleading.
