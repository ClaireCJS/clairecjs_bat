# PAFPlayer V673 — Local voice models

The independent model window downloads selected Piper, Kokoro, and Qwen models and creates comparable local speech samples and timing results. `--dj`, `--models`, `--model`, and `--install-models` open the window. Interactive first-install setup offers it as a skippable step. Model selection for the existing DJ remains Piper or OpenAI; comparison does not change playback settings.

Verification: 32 focused tests passed. The real Tk window opened and a real Piper run produced two comparison WAVs and results JSON. Kokoro and Qwen installation and comparison paths were mocked; their real downloads and synthesis were not tested. All 29 bundled modules compiled and matched editable sources; the release matches the active player. [Test report](../tests/reports/v673-voice-model-manager-checks-20261112.json).
