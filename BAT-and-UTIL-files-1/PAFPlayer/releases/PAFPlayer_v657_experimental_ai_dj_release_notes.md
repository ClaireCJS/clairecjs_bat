# PAFPlayer V657 — experimental AI Podcaster / DJ

The opt-in DJ prepares dialogue about recently heard track metadata in the background. `#dj` toggles it; `#djforce` requests or joins preparation and reports stages. The web **Experimental** section controls timing, cast, models, voices, accent instructions, and local fallback paths. Music resumes only when the DJ owned its pause. Explicit transport changes cancel the interruption.

OpenAI Responses and Realtime are the primary paths. Ollama provides local text fallback; Piper is the separate local speech fallback. The UI discloses cloud track-data sharing and AI-generated speech and links to Piper setup. No keys are displayed or stored in DJ settings. Output files are retained under the system temporary directory. FFplay uses its default output device for commentary.

## Verification

- 22 DJ tests and seven command-entry tests pass, including mocked provider failure, cancellation, settings security, and actual player pause/resume simulations.
- Player and 28 bundled modules compile; all 28 editable sources match their bundles; nine generated JavaScript blocks pass syntax checks.
- Three selected existing tests were compared against V656: the same web-pause source-contract test fails in both, while the other two pass.
- [Test report](../tests/reports/v657-dj-checks-20261111-164408.json); source SHA-256 `c0f3dbb7b92000df4866c5b8556b1af7286c678de025cb4009daec6114066b6f`.

## Limitations

Cloud calls were unreachable in the live smoke test. Ollama was not responding, and Piper was not installed; neither fallback was verified with real synthesis. The Realtime and Piper paths use mocked tests, and `websocket-client` is an optional dependency. Piper installation is manual through the linked guide. Provider voices do not guarantee gender or accent, and a prefetched segment reflects the history at preparation time. No literal C:\BAT path was changed.
