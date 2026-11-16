# PAFPlayer V720 — AI DJ provider precedence and Ollama diagnostics

The AI DJ conversation model uses five ordered provider dropdowns. Providers can be reordered or switched off, and duplicate selections swap positions. The player tries enabled providers in order and falls through after a failure. The defaults retain OpenAI first (which may use credits), followed by OpenRouter free GPT-OSS, the OpenRouter free router, Gemini only after free-tier confirmation, and local Ollama.

The standalone `PAFPlayer.py` now embeds the current DJ modules. `--ollamainstructions [model-name]` checks whether Ollama's process is present, whether its local API responds, which models the API exposes, the configured model-store path, and which model manifests are on disk. It gives next steps for each state. A responding API with no models is reported as a running service with an empty catalog; manifests hidden from that catalog prompt a model-store and permissions check. The command makes no downloads or model changes.

Validation: Python syntax compilation, standalone `--version`, bundle/source parity for the DJ modules, and a read-only `--ollamainstructions` run against the current local service.
