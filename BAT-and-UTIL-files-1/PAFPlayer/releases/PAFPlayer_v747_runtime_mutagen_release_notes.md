# PAFPlayer V747 — Mutagen ships with the runtime

Mutagen 1.47.0 is now pinned in requirements-core.txt and imported by the private runtime builder's verification step. Readiness checks treat it as required. This checkout's Python 3.12 runtime includes the verified Mutagen package and distribution metadata in runtime/Lib/site-packages, with its manifest updated. Self-installation copies this prepared runtime as before.

The playlist editor no longer downloads packages. It loads the shipped runtime dependency, or an already-completed offline cache for compatibility. Missing support produces an instruction to use the bundled runtime or update an incomplete installation.

Verification: offline dependency tests, playlist regressions, actual private-runtime import and FLAC tag round trip with networking blocked, syntax compilation, bundle parity and release-copy parity.
