# PAFPlayer V741 — Ctrl+Alt+P playlist toggle

Ctrl+Alt+P toggles the same playlist window as Alt+P during playback or pause, including when the playlist window itself has focus. The console handles printable, control-byte and extended scan-code encodings and uses a buffered-input gate to keep the shortcut focused on PAFPlayer. Existing P and Alt+P behavior is preserved.

Focused regression tests exercise console key decoding, modifier loss, the no-input focus gate and a Windows Tk shortcut event, along with existing playlist-window and bundle-parity checks. A physical keyboard on each Windows terminal variant was not tested.
