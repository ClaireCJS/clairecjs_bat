@Echo off

if defined emoji_play_button (%COLOR_SUCCESS% %+ echo %big_top%%emoji_play_button% %+ echo %big_bot%%emoji_play_button%)

::::: SETUP:
	call get-winamp-state


::::: BRANCHING:
	if "%1%"          eq    "play" goto :Play_YES
	if "%1%"          eq "unpause" goto :Play_YES
	if "%MUSICSTATE%" eq "PLAYING" goto :DoNothing
	if "%MUSICSTATE%" eq "STOPPED" goto :Play_YES
	if "%MUSICSTATE%" eq  "PAUSED" goto :Unpause_YES
	if "%MUSICSTATE%" eq "UNKNOWN" goto :Play_YES
	                               goto :Play_YES


goto :END


		:Unpause_YES
			call unpause %*
		goto :END


		:Play_YES

			if "%1"=="exit" call less_important "Attempting to start music via WinAmp WAWI web interface, using %italics_on%wget%italics_off%..."
                    %COLOR_LOGGING% 
                    call wget32    --tries=3 --wait=1 --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% --spider http://%TMPMUSICSERVER/play
                    %COLOR_NORMAL%  
                    call get-winamp-state
			if "%BOTH"=="1" call wget32    --tries=3 --wait=1 --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% --spider http://%TMPMUSICSERVER/play

			if /i "%1"=="exit"      exit
			if /i "%1"=="exitafter" exit
		goto :END


:END
:DoNothing

