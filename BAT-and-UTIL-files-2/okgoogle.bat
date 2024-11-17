@echo off
 call get-winamp-state
 set ORIGINAL_MUSIC_STATE=%MUSICSTATE%
 if "%MUSICSTATE%" eq "PLAYING" (call stop %+ SET MUSICSTATE=STOPPED)
 call speak       OK google. ... %*
 if "%ORIGINAL_MUSIC_STATE%" eq "PLAYING" (call play     )
 if "%ORIGINAL_MUSIC_STATE%" eq "PAUSED"  (REM do nothing)
 if "%ORIGINAL_MUSIC_STATE%" eq "STOPPED" (REM do nothing)
