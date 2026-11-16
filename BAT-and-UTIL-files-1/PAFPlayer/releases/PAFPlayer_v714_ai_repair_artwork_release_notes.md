# V714 — AI repair guide, model storage and tag-editor artwork

- Add `--ai`, a console workflow that checks provider-key presence without exposing values, local Ollama visibility, Piper files, and the configured model location. It offers a live text comparison using free providers only (never the paid OpenAI model) and can open the model manager for explicit download/comparison actions.
- Add a saved AI DJ **Model storage folder** field. The selected location is shared with model downloads and Piper setup. Changing locations requires the model manager’s **Move models** action to copy, verify and link existing stores.
- Add embedded album-art preview and replacement to the single-track playlist tag editor. Replacement and tag writes retain a verified timestamped sibling backup of the original audio file.

The host already had the model stores at `T:\\models`: `%LOCALAPPDATA%\PAFPlayer\support\voice-models`, `%LOCALAPPDATA%\PAFPlayer\support\piper`, and `%USERPROFILE%\.ollama\models` are junctions into that directory. No model files were moved during this release.

Verification: syntax compilation and bundle/source parity are checked; no live model calls, downloads, tag edits, or file moves are performed during implementation.
