# PAFPlayer V727 — Private Python runtime

First-run installation now selects `C:\util\PAFPlayer`, with the existing collision-safe versioned names and `%LOCALAPPDATA%` fallback when `C:\util` is unavailable. The installer stages `pafplayer.bat`, a pinned core dependency manifest, and a prebuilt runtime when present. Existing destinations are preserved.

`pafplayer.bat` prefers the app-owned interpreter. `tools/build_private_runtime.py` downloads the official 64-bit Windows Python 3.12.10 installer, creates an app-local runtime with Tcl/Tk support, installs pinned core packages into its private `site-packages`, verifies imports, records a hash manifest, and refuses to overwrite an existing runtime. No virtual environment is created. Qwen/Piper packages and model weights remain separate optional installs.

The runtime builder must run on 64-bit Windows with network access, or an already downloaded official Python installer. This change updates the source project and documentation only; no installed runtime has been built or deployed.
