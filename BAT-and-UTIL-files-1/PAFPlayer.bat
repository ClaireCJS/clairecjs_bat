@Echo OFF


rem Set our beta/production status:
        set PAFPLAYER_STATUS=PRODUCTION
        set PAFPLAYER_STATUS=BETA


rem Run the proper version:
        if "%PAFPLAYER_STATUS%" == "BETA"       c:\codex\clairevironment\bat\PAFPlayer\PAFPlayer.py %*
        if "%PAFPLAYER_STATUS%" == "PRODUCTION"                         %BAT\PAFPlayer\PAFPlayer.py %*




