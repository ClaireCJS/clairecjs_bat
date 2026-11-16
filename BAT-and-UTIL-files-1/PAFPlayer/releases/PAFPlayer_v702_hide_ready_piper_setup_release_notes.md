# PAFPlayer V702 release notes

## Piper setup control

The AI DJ web panel now hides **Download / repair free Piper voices** when either of these is true:

- the private automatic Piper install has both its executable and at least one voice model; or
- a configured Piper executable and one or more configured voice model files are available, with no configured paths missing.

The control remains available when setup is missing, incomplete, or needs repair. The readiness check runs with the existing DJ status polling and does not download, modify, or remove any voice files.

## Verification

- Embedded `PlayWaveFileTests.test_v702_hides_ready_piper_setup_button` passed.
- Active `PAFPlayer.py` was syntax-compiled without writing bytecode.
