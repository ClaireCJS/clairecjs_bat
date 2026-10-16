# PAFPlayer V468

- Made the web **Tags** section functional with an explicit **Expand all tags**
  button. It loads the complete current-track metadata list, reports the count,
  and toggles cleanly back to a collapsed view.
- Embedded-art tag fields (ID3 APIC, MP4 covr, and FLAC-style picture fields)
  now show the resolved cover image in the Tags view instead of emitting a raw
  binary or base64 payload.
- Removed the accidental dependency on the first unrelated HTML `details`
  element, which was why the Tags section previously appeared inert.
