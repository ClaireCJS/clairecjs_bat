# PAFPlayer V672 — Piper startup preparation

Prepare free local Piper voices in the background when AI DJ starts. The DJ tab displays detected model paths and setup progress and offers a retry button. Missing custom executable or model paths fall back to working automatic paths. Installations are serialized so startup and speech synthesis do not race.

Verification: 82 focused tests passed; browser checks covered Piper setup, prompt and sleep controls. The existing local Piper installation synthesized real audio at 22050 Hz. Eleven JavaScript blocks and 28 bundled modules passed checks; the release matches the active player. The new context was not tested against a live text provider. [Test report](../tests/reports/v672-dj-variety-piper-checks-20261112.json).
