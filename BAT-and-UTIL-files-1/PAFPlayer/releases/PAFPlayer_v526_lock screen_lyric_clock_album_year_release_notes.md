# PAFPlayer V526 release notes

Released October 11, 2026.

The Windows lock-screen detailed status now requests these rows:

1. `Artist – Song`
2. `elapsed/total · current lyric`
3. `Album (year)`

The title separator is an en dash. Year is read from Year/year and then Date/date
metadata; a leading four-digit year is used when a longer date is present. Empty
years omit the parentheses. The compact lock-screen endpoint now carries those
metadata fields, and the publication cache includes both newly composed rows so
lyric, album, year, and counter changes trigger an update.
