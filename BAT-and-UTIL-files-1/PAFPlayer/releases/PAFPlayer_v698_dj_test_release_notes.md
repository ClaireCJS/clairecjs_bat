# V698 — DJ text-model comparison

Run `--dj-test [playlist]` to simulate the configured DJ interval and compare the same live prompt and context across available free providers and installed Ollama models. An authenticated snapshot reads an existing player playlist without changing it. Older players can supply the playlist via their local web interface. Use `--include-paid` to opt in to the configured OpenAI model; that can consume credits. Hosted providers receive the selected track metadata and lyrics. Model availability and provider failures are reported individually.
