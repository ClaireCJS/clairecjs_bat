# PAFPlayer V662 — free DJ providers and credit warnings

Text fallback adds OpenRouter's free router and Gemini's free-eligible model before Ollama. Gemini is skipped unless the user explicitly confirms the Google project is on the free tier; a paid project can incur charges. Local Piper remains the speech fallback. Keys come from private.env or the process environment; artist/title metadata is sent to the selected hosted service.

The exact OpenAI `credit_balance_exhausted` error creates a persistent key-scoped warning in Help and the bottom Warnings web tab; ordinary rate limits do not. A later successful OpenAI text request clears the warning. Free-provider availability and credentials require separate verification.
