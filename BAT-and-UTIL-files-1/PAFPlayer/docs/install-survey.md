# First-install survey rehearsal (V595)

Run `python PAFPlayer.py --install-survey-dry-run` in an interactive Windows
terminal. This is a rehearsal of choices for a later first-install wizard. It
warns that there may be many questions. It does not start audio, contact the
running player, change a playlist, or apply answers to active settings. With
missing or redirected stdin it exits before reading configuration. The switch
must be used alone. A future real installation survey is separate work.

The ten skippable sections cover playback/output, volume and bass, console
visualizer, karaoke/Emojimaxx, floating windows, web configuration, alerts,
Windows integration, experimental features, and remote/tray behavior. The
catalog uses existing player and web configuration IDs. It deliberately omits
ordinary playback speed, volume, balance, always-on artwork and visualizer
bars, duplicate advanced artwork controls, and the tray enable switch. Console
visualizer choices appear in their own section. The portable Developer's
Choice (`PAFPlayer.dcc`) supplies displayed defaults when present; decensored
karaoke defaults on when that file has no explicit value.

Each question explains its effect, displayed default, current saved value, and
saved favorites when present. Preset choices use ↑/↓ and Enter in a native
Windows terminal; Enter always selects the highlighted choice. A favorite
shortcut appears only when a favorite exists. Text questions show the valid
range and examples. Output rates display kHz (for example, `192` for
192 kHz). Silence/overlap is entered in seconds (for example, `-1.5` means
1.5 seconds of overlap). Bass boost/reduction is one signed percentage
question (`0`, `+25%`, `-30%`); locked-computer reduction is one separate
percentage question. Selected results appear in bright green. `S` skips a
question; `A` asks whether to skip the current section or abort the whole
survey. At each section boundary, Enter continues, `S` skips the section,
`F` finishes early with displayed defaults for unanswered questions, and
`A` asks what to abort.

The integration questions explain Last.fm, Discord, MonkeyMote, web uploads,
the screensaver, and the lock-screen companion. Last.fm can test credentials
only after you explicitly request a test; the test authenticates but does not
scrobble. The survey does not save the password, API secret, or session key.
Discord setup covers Desktop IPC, Social SDK, and Automatic. The survey can
validate an Application ID's format but cannot complete Social SDK setup
without Discord's official SDK and authorization. It can optionally test a
Discord Desktop IPC handshake without posting activity. MonkeyMote defaults to on
and offers extended phone/tablet setup instructions. Web uploads are described
as a security-sensitive choice. The tray symbol and color use existing icon
style IDs; the tray stays enabled by default.

Screensaver and lock-screen setup are **previews** unless you type the exact
override phrase shown in that section. `INSTALL SCREEN SAVER` invokes Windows'
screensaver Install action. `TEST SCREEN SAVER` starts a bounded local preview
with a synthetic lyric for at most ten seconds. `INSTALL LOCK SCREEN` invokes
the existing bundled companion installer. These explicit overrides can make
real OS changes during a dry run; the survey announces that boundary before
asking. The lock-screen installer does not change UAC. If UAC is disabled, an
explicit install request is recorded for retry on a later normal player launch
after UAC has been enabled and Windows rebooted. The user previously chose to
leave UAC disabled, so no UAC change is performed. Windows controls what the
secure lock screen displays: this companion cannot force arbitrary live art
and lyrics onto the sign-in screen. A synthetic lock-screen lyric preview is
not available; use a manual Win+L visual check after installation instead.

The final summary shows proposed changes. You may discard, restart, or save a
**new** named Global Config profile. Saving requires typing `SAVE <name>`
exactly. Profiles use the existing
`%LOCALAPPDATA%\PAFPlayer\global-config-profiles-v446.json` format and verified
backup/atomic-write path. The survey never activates a profile automatically.
Loading immediately afterward requires `L`, then `LOAD <name>`, then
`APPLY <name>`; only this twice-confirmed load invokes the existing loader.
The saved setup plan is inert and omits credentials. Registry defaults and
favorites, MatrixMixer state, playback, and playlist resume data are excluded.
Abort, Ctrl+C, EOF, and closing the terminal before a confirmed save leave no
partial settings changes. Explicit OS install overrides are the sole exception
and cannot be undone by discarding the survey.
