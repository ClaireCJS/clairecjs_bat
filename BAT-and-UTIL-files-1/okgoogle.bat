@echo on
@on break cancel
 call get-winamp-state
 set ORIGINAL_MUSIC_STATE=%MUSICSTATE%
 if "%MUSICSTATE%" eq "PLAYING" (call stop %+ SET MUSICSTATE=STOPPED)
 call speak       OK google. ... %*
 if "%ORIGINAL_MUSIC_STATE%" eq "PLAYING" (call play     )
rem  if "%ORIGINAL_MUSIC_STATE%" eq "PAUSED"  (REM do nothing)
rem  if "%ORIGINAL_MUSIC_STATE%" eq "STOPPED" (REM do nothing)
