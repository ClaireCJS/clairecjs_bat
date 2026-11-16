# V719 — AI provider order and staged Ollama guidance

- Replace the AI DJ’s single text-provider selector with five ordered priority dropdowns. Set individual slots to Off; selected providers are tried in order after failures, and duplicate choices swap slots automatically. The default is OpenAI, free OpenRouter GPT-OSS, free OpenRouter router, Gemini after free-tier confirmation, and local Ollama. The UI labels possible OpenAI charges and Gemini’s free-tier requirement.
- Keep old saved provider selections working by translating their previous mode into an equivalent ordered list. Autosave and AI DJ profiles retain the new order.
- Make `--ollamainstructions` check process presence, API reachability, visible models, the configured model directory, and on-disk manifests. It reports the next repair step for the current state rather than repeating generic setup instructions.
- Show the configured provider order in AI DJ diagnostics and text-model comparisons.

No model downloads or generation requests are started by `--ollamainstructions`.
