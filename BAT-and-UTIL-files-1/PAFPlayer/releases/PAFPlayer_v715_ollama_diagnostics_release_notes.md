# V715 — Ollama diagnostics wording

- Distinguish an unreachable Ollama API from a running Ollama server that returns an empty model catalog.
- When model files exist but the API lists zero models, direct users to the active daemon’s `OLLAMA_MODELS` location and permissions. Recommend a restart only after correcting that setting.
- Remove unnecessary Ollama installation/start instructions when the service is already responding.

On the current host, `ollama` and `ollama app` processes are present, `/api/tags` and `/api/ps` respond, and both APIs report an empty model list. Manifests for GPT-OSS 120B and two Qwen models exist in `T:\models\Ollama`. No model or Ollama process was changed.
