# PAFPlayer V661 — DJ private key loading

The DJ reads a valid `OPENAI_API_KEY` from `C:\BAT\private.env` when available, with the process environment as a fallback. The private-file value takes priority over stale inherited keys. The key is never written into DJ settings or diagnostics.

The new service-account key authenticated against the models endpoint, but a live text request returned HTTP 429 `credit_balance_exhausted`, so cloud generation was not verified. Ollama and Piper remain the local fallback. A verified backup of the prior private environment file was created before the file was updated. Two key-loading tests, six DJ diagnostic and playback tests, and 36 existing Piper, Help, DJ, and command tests passed. All 28 bundled modules compiled and the release matched the active player. [Test report](../tests/reports/v661-dj-private-key-checks-20261111.json).
