@Echo OFF
@on break cancel
@LoadBTM on

rem Config:
        set PAFPLAYER_TO_USE_RIGHT_NOW=%BAT%\PAFPlayer-sandbox\PAFPlayer.py
        set PAFPLAYER_TO_USE_RIGHT_NOW=%BAT%\PAFPlayer.bat




rem Check environment:
        if defined MUSICSERVERMACHINENAME .and. defined MUSICSERVERPORT .and. defined BAT .and. exist "%PAFPLAYER_TO_USE_RIGHT_NOW%" goto :environment_probably_fine


        if not defined BAT                         call validate-environment-variable BAT
        if not defined MUSICSERVERPORT             call validate-environment-variable MUSICSERVERPORT
        if not defined MUSICSERVERMACHINENAME      call validate-environment-variable MUSICSERVERMACHINENAME
        if not  exist  PAFPLAYER_TO_USE_RIGHT_NOW  call validate-environment-variable PAFPLAYER_TO_USE_RIGHT_NOW                

        :environment_probably_fine



rem Actually do it:        
        %PAFPLAYER_TO_USE_RIGHT_NOW% --tray-only %MUSICSERVERMACHINENAME%:%MUSICSERVERPORT% --floating-lyrics --album-art --art-lyrics
        rem CLI OPS not used: --floating-lyrics-always-on-top 