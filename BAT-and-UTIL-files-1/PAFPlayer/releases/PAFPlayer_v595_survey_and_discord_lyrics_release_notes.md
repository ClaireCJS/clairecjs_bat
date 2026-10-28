# PAFPlayer V595 — Install survey rehearsal and Discord lyrics

The `--install-survey-dry-run` rehearsal now offers color, arrow-key preset
selection in a native Windows terminal, clearer Enter/selection feedback, and
an abort choice between the current section and the whole survey. It reads
Developer's Choice defaults, shows saved favorites only when present, presents
output rates in kHz and track overlap in seconds, and combines bass enablement
with signed percentage amounts. Console visualizer choices have their own
section. The catalog omits controls that are always enabled or unsuitable for
initial setup.

Guided questions cover Last.fm, Discord connection method, MonkeyMote, web
upload security, tray symbol/color, screensaver, and lock-screen companion.
The Last.fm test requires an explicit request, performs authentication only,
and does not store the password, API secret, or session key. Normal survey
answers remain a proposal. Saving a named profile requires an exact
confirmation; loading it requires two more confirmations.

Exact typed Windows overrides can invoke screensaver installation, a bounded
synthetic-lyric screensaver preview, or lock-screen companion installation
while the survey is otherwise a dry run. With UAC disabled, an explicit
lock-screen install request is remembered and retried at the next normal
player launch after UAC becomes available. PAFPlayer does not change UAC.
Windows lock-screen status APIs do not provide arbitrary timed artwork/lyric
rendering on the secure screen, so that visual result still requires manual
verification. A synthetic lock-screen preview is not implemented.

Discord activity uses line 1 for `🎵 Song · 👩‍🎤 Artist · 💿 Album (YYYY)` and
line 2 for `🎤 current lyric`, or exactly `🎤 ♪` when no lyric is available.
Missing metadata is omitted and long text is truncated to Discord's activity
limits. Paused playback retains the current activity, stopped or private
playback clears it, and a changing animation progress value alone does not
republish it. Desktop IPC and Social SDK use the same payload. The separate
Discord application name remains `PAFPlayer`. The local-title sharing option
now explicitly describes that albums and lyrics are also shared.

Focused automated tests verify survey safety, explicit override boundaries,
deferred lock-screen retry, Discord payloads, privacy clearing, and lyric
transitions. A real lock-screen installation, physical screensaver preview,
and native Social SDK publication still need live Windows/Discord validation.
