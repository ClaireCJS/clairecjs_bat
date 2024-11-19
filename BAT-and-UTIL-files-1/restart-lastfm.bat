@echo off
@on break cancel
kill /f last*
:call KillifRunning LASTFM~1 LASTFM~1
call    lastfm-start
