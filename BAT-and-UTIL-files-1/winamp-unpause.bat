@Echo OFF
@on break cancel
@if "%1" == "quick" .or. "%1" == "quickly" (set UNPAUSE_QUICKLY=1 %+ goto :Unpause_Quickly)

if defined emoji_play_button (%COLOR_SUCCESS% %+ echo %big_top%%emoji_play_button% %+ echo %big_bot%%emoji_play_button%)


::::: SETUP:
	: Not necessary because all branched scripts
    : do this as their setup anyway: 

    :2017: update: no they don't! we need this!


::::: CHECK WINAMP STATE TO REACT, OR SKIP THAT STUFF:
    call get-winamp-state


::::: BRANCHING:
	if "%MUSICSTATE%" == "PLAYING" goto :DoNothing
	if "%MUSICSTATE%" == "STOPPED" goto :Play_YES
	if "%MUSICSTATE%" ==  "PAUSED" goto :Unpause_YES
	if "%MUSICSTATE%" == "UNKNOWN" goto :Unpause_YES
	                               goto :Unpause_YES

goto :END

                :Unpause_Quickly
                        call winamp-pause quick %2$
                goto :END

		:Unpause_YES					
			call winamp-pause OVERRIDE %*
		goto :END

		:Play_YES		
                        if "1" == "%PAF_WINAMP_INTEGRATION%" (call winamp-play %* >&>nul)
			if "1" != "%PAF_WINAMP_INTEGRATION%" (call winamp-play %*       )
		goto :END


:END
:DoNothing
