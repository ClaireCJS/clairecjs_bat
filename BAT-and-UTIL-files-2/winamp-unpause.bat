@Echo OFF

if defined emoji_play_button (%COLOR_SUCCESS% %+ echo %big_top%%emoji_play_button% %+ echo %big_bot%%emoji_play_button%)


::::: SETUP:
	: Not necessary because all branched scripts
    : do this as their setup anyway: 

    :2017: update: no they don't! we need this!


::::: CHECK WINAMP STATE TO REACT, OR SKIP THAT STUFF:
    if "%1" eq "quick" .or. "%1" eq "quickly" (set UNPAUSE_QUICKLY=1 %+ goto :Unpause_Quickly)
    call get-winamp-state


::::: BRANCHING:
	if "%MUSICSTATE%" eq "PLAYING" goto :DoNothing
	if "%MUSICSTATE%" eq "STOPPED" goto :Play_YES
	if "%MUSICSTATE%" eq  "PAUSED" goto :Unpause_YES
	if "%MUSICSTATE%" eq "UNKNOWN" goto :Unpause_YES
	                               goto :Unpause_YES

goto :END

        :Unpause_Quickly
            call winamp-pause quick
        goto :END

		:Unpause_YES					
			call winamp-pause OVERRIDE %*
		goto :END

		:Play_YES					
			call winamp-play %*
		goto :END


:END
:DoNothing
