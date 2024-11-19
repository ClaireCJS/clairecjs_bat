@Echo OFF
 on break cancel

if defined emoji_stop_button (%COLOR_REMOVAL% %+ echo %big_top%%emoji_stop_button% %+ echo %big_bot%%emoji_stop_button%)

if "%1" eq "fast" goto :fast

::::: SETUP:
	call get-winamp-state


::::: BRANCHING:
	if "%MUSICSTATE%" eq "PLAYING" goto :Stop_YES
	if "%MUSICSTATE%" eq "STOPPED" goto :DoNothing
	if "%MUSICSTATE%" eq  "PAUSED" goto :DoNothing
	if "%MUSICSTATE%" eq "UNKNOWN" goto :Stop_YES
	                               goto :Stop_YES

goto :END


		:Stop_YES
        :fast
			:call setTmpMusicServer.bat %*
				            :call wgetquiet                         --user=%WAWI_USERNAME%    --password=%WAWI_PASSWORD% --spider http://%TMPMUSICSERVER%/stop
					         call wget32    --tries=3 --wait=1 --http-user=%WAWI_USERNAME% --http-passwd=%WAWI_PASSWORD% --spider http://%TMPMUSICSERVER%/stop
			:if "%BOTH"=="1" call wgetquiet                         --user=%WAWI_USERNAME%    --password=%WAWI_PASSWORD% --spider http://%TMPMUSICSERVER2/stop
			 if "%BOTH"=="1" call wget32    --tries=3 --wait=1 --http-user=%WAWI_USERNAME% --http-passwd=%WAWI_PASSWORD% --spider http://%TMPMUSICSERVER%/stop
		goto :END


:END
:DoNothing

if "%1" eq "fast" goto :fast2
    call get-winamp-state
:fast2

