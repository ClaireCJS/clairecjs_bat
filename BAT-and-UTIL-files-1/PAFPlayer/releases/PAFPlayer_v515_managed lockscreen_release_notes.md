# PAFPlayer V515 — managed lock-screen publisher

PAFPlayer now starts, configures, restarts and stops its optional signed Windows
publisher automatically. A web-setting checkbox uses the preserved
PAFPlayerLockScreenEnabled key. Existing explicit companion preferences migrate;
fresh installs remain disabled. The helper is headless, pins the official local
player identity, and sends no playback commands. All activation work runs outside
the audio/render loops. Windows app activation replaces a direct executable
launch that failed with access denied on this machine.

**This release does not claim the remaining blank native lock screen is fixed.**
Automatic lifecycle, installed-package activation and publication passed actual
interactive checks. Native visible rendering still awaits the user's check.
UAC remains unchanged and disabled. The currently playing V514 process was not
restarted; automatic management starts with the next V515 player launch.

120 focused tests passed. The full 678 embedded tests ran on V515 and unchanged
V514: both had the same 51 failures and 13 errors (614 passes). No new failing
test names appeared; these results are not a clean full-suite pass. Compilation,
full package validation, signatures, interactive activation/publication, headless
launch, session pinning and graceful shutdown passed. Scheduled timer execution
and locked-screen appearance remain unverified.

The installed package is 515.0.0.1, displayed as PAFPlayer Lock Screen V515.
Family/App ID and earlier configuration IDs are preserved. Earlier releases and
build candidates remain intact. play_audio_file.py was not changed.

No literal C:\BAT paths were created, modified or deleted.

See the [architecture, limitations and manual verification](../docs/windows-lock-screen.md).
