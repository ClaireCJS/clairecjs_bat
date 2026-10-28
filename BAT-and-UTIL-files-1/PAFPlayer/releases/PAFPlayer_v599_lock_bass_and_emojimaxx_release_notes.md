# PAFPlayer V599 release notes

## Locked-session bass default

The existing **Reduce bass while computer is locked** switch now defaults to on
at 50% when no `ReduceBassWhenLocked` setting exists. Previously saved off/on
choices remain authoritative. The web page reads that effective saved choice
when it first opens, and the existing command-line overrides remain session
only. Turning the switch off restores the ordinary unlocked bass treatment;
Windows lock-screen song and lyric status remain independently enabled or
disabled by their own setting.

## Emojimaxx wording

Emojimaxx leaves the word `heavy` in lyrics rather than replacing it with a
mechanical-arm emoji. Directional arrow glyphs and other substitutions remain.

## Verification and limits

Five new regression tests passed for defaults, saved settings, command-line
precedence, web initialization, and lyric rendering. Twelve V590 and eleven
V591 bass tests passed, including decoded PCM checks; seven earlier relevant
tests passed. Python source and test syntax checks passed. These tests did not
perform a new audible Windows lock/unlock listening test. The existing test
suite emitted an unrelated Steam monitor `atexit` warning after passing.

The Chrome video lock-screen/widget priority TODO remains open: Windows chooses
which media session owns that surface, and this release does not change it.
