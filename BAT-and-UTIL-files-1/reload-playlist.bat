@Echo off
@on break cancel


:DESCRIPTION: Tries to use Winamp's WAWI web interface to reload a playlist, for the case of a playlist modified after load
:DESCRIPTION: Very much relies on the playlist being stored with playlist.bat, so is absolutely not reliable for manually-reloaded playlists
:DESCRIPTION:  But *is* reliable for command-line-loaded playlists.















call setTmpMusicServer.bat %* %+ rem Deprecated 2-floor-separate-audio stuff


:OLD: set PLAYLIST=%@LINE[%TMPMP3\LISTS\now-playing.dat,0]
:NEW:
      set PLAYLIST=%TMPMP3\LISTS\now-playing-playlist.m3u
echo *** PLAYLIST is now %PLAYLIST


:call playlist %PLAYLIST nonext %*
 call playlist %PLAYLIST %*



call setTmpMusicServer.bat %*
if "%BOTH"=="1" goto :both
goto :end



:both
call setTmpMusicServer.bat %*
:OLD: set PLAYLIST=%@LINE[%TMPMP32\LISTS\now-playing.dat,0]
      set PLAYLIST=%TMPMP32\LISTS\now-playing-playlist.m3u
      set PLAYLIST=now-playing-playlist
echo PLAYLIST is now %PLAYLIST
call playlist %PLAYLIST nonext %*

:end

