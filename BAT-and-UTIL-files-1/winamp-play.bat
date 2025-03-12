@Echo off
 on break cancel

::::: DISPLAY A PLAY BUTTON:
        :retry_1
        iff not defined emoji_play_button then
                call set-emoji force
                call set-ansi  force
        endiff
        if  not defined emoji_play_button call error "play button emoji still not defined"
        iff defined emoji_play_button .and. "1" != "%retried_pb_already%" .and. "1" != "%PAF_WINAMP_INTEGRATION%"  then
                echo %ANSI_COLOR_SUCCESS%%big_top%%emoji_play_button% %+ echo %big_bot%%emoji_play_button%
                set  retried_pb_already=1
                goto :retry_1
        endiff

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
                        if "%1"=="exit" call less_important "Attempting to start music via WinAmp WAWI web interface, using %italics_on%wget%italics_off%..."             %+  echos %ansi_COLOR_LOGGING% 
                        call                   wget32    --tries=3 --wait=1 --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% --spider http://%TMPMUSICSERVER/play        %+  echos %ansi_COLOR_NORMAL%%ANSI_ERASE_TO_EOL%
                        call   get-winamp-state
                        if "%BOTH" == "1" call wget32    --tries=3 --wait=1 --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% --spider http://%TMPMUSICSERVER/play
                        if /i "%1" == "exit" .or. "%1" == "exitafter" exit
		goto :END


:END
:DoNothing

