# PAFPlayer V675 — Voice model installation progress

The model window shows streamed installer output, elapsed time, current-step and overall model progress. Direct model downloads display bytes and speed, with a percentage when available. Piper setup also forwards subprocess output. Unknown-duration stages use an animated bar.

Verification: 82 focused regression tests passed, including six progress and Piper streaming checks. Real Tk window probes displayed byte-based and installer-reported percentages; real subprocess output was visible before exit, and real Piper comparison still worked. All 29 bundled modules matched editable sources, and the release matches the active player. A live large-model download was not performed. [Test report](../tests/reports/v675-model-progress-checks-20261112.json).
