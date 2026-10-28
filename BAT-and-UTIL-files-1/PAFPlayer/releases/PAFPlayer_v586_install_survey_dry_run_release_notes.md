# PAFPlayer V586 — first-install survey dry run

Released October 20, 2026.

Run `python PAFPlayer.py --install-survey-dry-run` in an interactive terminal.
This is a rehearsal, warns about its many questions, and reaches no playback,
tray, single-instance IPC, setup, or lock-screen startup path. Missing stdin/TTY
and conflicting command-line options exit without changes.

Ten skippable sections cover playback/output, volume/bass, visualizer,
karaoke/Emojimaxx, artwork/floating windows, web configuration, alerts,
Windows integration, experiments, and remote/tray behavior. Each question
explains the control, shows the current default, saved value, favorites when
present, and valid answers. A section can be skipped or aborted, or the survey
can finish early by assuming defaults for remaining questions. The final
summary lists proposed changes. Discard, restart, and a confirmed named-profile
save are available.

The save uses the existing Global Config profile format and store. It rejects
reserved or conflicting names and requires typing `SAVE <name>`. It does not
activate the profile. A separate post-save load requires requesting it and
typing both `LOAD <name>` and `APPLY <name>`; only then does the established
profile loader write active settings. All survey reads, including legacy
registry values, avoid lazy migration. A survey profile includes current player
settings and web preferences plus the proposed answers, while leaving
MatrixMixer, registry choice marks, runtime state, and playlist resume outside
its payload. The existing verified backup path protects a profile store that
already exists.

The focused V586 suite covers read-only behavior, defaults/favorites, skip,
abort, finish-early, validation, confirmation, double-confirmed load, and
noninteractive safety. See `docs/install-survey.md` for exact inputs. Remote
tray-only machine settings, lock-screen registration, FFmpeg installation,
device tests, and a real first-install wizard remain separate work because
they cannot be safely rehearsed as portable saved profile choices.
