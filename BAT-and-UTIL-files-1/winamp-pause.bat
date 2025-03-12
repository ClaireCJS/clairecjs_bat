@if "%1" == "quick" .or. "%1" == "quickly" (set PAUSE_QUICKLY=1 %+ goto :Pause_Quickly_1)


@Echo off
@on break cancel



rem Validate environment (once):
        if defined emoji_pause_button (echo %ansi_color_normal%%big_top%%emoji_pause_button% %+ echo %big_bot%%emoji_pause_button%)
        if "%MUSIC_AND_GIRDER_SEVERS_VALIDATED" == "1" (goto :Skip_Music_and_Girder_Server_Validation)
                call validate-environment-variables MUSICSERVERIPONLY TMPMUSICSERVER GIRDERPORT GIRDERPASSWORD WAWI_USERNAME WAWI_PASSWORD
        :Skip_Music_and_Girder_Server_Validation

rem Set values to use:
       :Pause_Quickly_1
        set USERNAME_PAUSE=%WAWI_USERNAME%
        set PASSWORD_PAUSE=%WAWI_PASSWORD%
        if "1" == "%PAUSE_QUICKLY" goto :Pause_Quickly

rem Get the current winamp state:
        call get-winamp-state silent

rem Branch accordingly:
        if "%1"           == "OVERRIDE" goto :Pause_YES
        if "%MUSICSTATE%" ==  "PLAYING" goto :Pause_YES
        if "%MUSICSTATE%" ==  "STOPPED" goto :DoNothing
        if "%MUSICSTATE%" ==   "PAUSED" goto :DoNothing
        if "%MUSICSTATE%" ==  "UNKNOWN" goto :Pause_YES
                                        goto :Pause_YES                 %+ REM //default cause
        goto :END


                      




	:Pause_YES					
		rem OLD 2-floor code: call setTmpMusicServer.bat %*
		if "%1"=="2" .OR. "%2"=="2" goto :Pause_YES_Two_Floors
				            goto :Pause_YES_One_Floor
	:Pause_NO

                :Pause_YES_One_Floor
                :Pause_Quickly
			@		    call wget32    --tries=3 --wait=1 --http-user=%USERNAME_PAUSE% --http-passwd=%PASSWORD_PAUSE% --spider http://%TMPMUSICSERVER%/pause
                        @unset /q PASSWORD_PAUSE
                        @if "%PAUSE_QUICKLY%" == "1" (goto :END_Quickly)
                        @color magenta on black
                        @call advice "(If that didn't work, try 'paus 2' to do it with Girder instead of WAWI.)"
                        @set UNDOCOMMAND=unpause
                        @set REDOCOMMAND=pause.btm %*
                @goto :END


                                            :Pause_YES_Two_Floors
                                                call less_important "Trying with girder..."
                                                girder-internet-event-client %MUSICSERVERIPONLY %GIRDERPORT %GIRDERPASSWORD WINAMP_PAUSE whatever
                                                call debug "(If that didn't work, try 'paus' without the 2 after it to do it with WAWI instead of Girder.)"
                                                set UNDOCOMMAND=unpause
                                                set REDOCOMMAND=pause.btm %*
                                            goto :END


:END
:DoNothing
@call get-winamp-state
@if defined PAUSE_QUICKLY unset /q PAUSE_QUICKLY
:END_Quickly
@if "%1" == "exitafter" .or. "%2" == "exitafter" (exit)