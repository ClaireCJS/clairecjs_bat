@Echo off
 on break cancel

if "%1" eq "quick" .or. "%1" eq "quickly" (set PAUSE_QUICKLY=1 %+ goto :Pause_Quickly)

if defined emoji_pause_button (%COLOR_NORMAL% %+ echo %big_top%%emoji_pause_button% %+ echo %big_bot%%emoji_pause_button%)

if "%MUSIC_AND_GIRDER_SEVERS_VALIDATED" eq "1" (goto :Skip_Music_and_Girder_Server_Validation)
        call validate-environment-variables MUSICSERVERIPONLY TMPMUSICSERVER GIRDERPORT GIRDERPASSWORD WAWI_USERNAME WAWI_PASSWORD
:Skip_Music_and_Girder_Server_Validation


set USERNAME_PAUSE=%WAWI_USERNAME%
set PASSWORD_PAUSE=%WAWI_PASSWORD%


call get-winamp-state silent

if "%1"           eq "OVERRIDE" goto :Pause_YES
if "%MUSICSTATE%" eq  "PLAYING" goto :Pause_YES
if "%MUSICSTATE%" eq  "STOPPED" goto :DoNothing
if "%MUSICSTATE%" eq   "PAUSED" goto :DoNothing
if "%MUSICSTATE%" eq  "UNKNOWN" goto :Pause_YES
                                goto :Pause_YES                 %+ REM //default cause


goto :END















	:Pause_YES					
		:call setTmpMusicServer.bat %*
		if "%1"=="2"          .OR. "%2"=="2" goto :Pause_YES_Two_Floors
						     goto :Pause_YES_One_Floor
	:Pause_NO

		:Pause_YES_One_Floor
            :Pause_Quickly
			if "%BOTH"=="1"    call wgetquiet --tries=3 --wait=1      --user=%USERNAME_PAUSE%    --password=%PASSWORD_PAUSE% --spider http://%TMPMUSICSERVER2/pause
                  :    echo    call wgetquiet --tries=3 --wait=1      --user=%USERNAME_PAUSE%    --password=%PASSWORD_PAUSE% --spider http://%TMPMUSICSERVER%/pause
				  :            call wgetquiet --tries=3 --wait=1      --user=%USERNAME_PAUSE%    --password=%PASSWORD_PAUSE% --spider http://%TMPMUSICSERVER%/pause
					           call wget32    --tries=3 --wait=1 --http-user=%USERNAME_PAUSE% --http-passwd=%PASSWORD_PAUSE% --spider http://%TMPMUSICSERVER%/pause
            unset /q PASSWORD_PAUSE
            if "%PAUSE_QUICKLY%" eq "1" (goto :END_Quickly)
            color magenta on black
			call advice "(If that didn't work, try 'paus 2' to do it with Girder instead of WAWI.)"
            set UNDOCOMMAND=unpause
            set REDOCOMMAND=pause.btm %*
		goto :END


                                            :Pause_YES_Two_Floors
                                                call less_important "Trying with girder..."
                                                :Pause_YES_Two_Floors-floors-with-different-music setup:
                                                :                               girder-internet-event-client %TMPMUSICSERVER    %GIRDERPORT %GIRDERPASSWORD WINAMP_PAUSE whatever
                                                :if "%BOTH"=="1"               (girder-internet-event-client %TMPMUSICSERVER2   %GIRDERPORT %GIRDERPASSWORD WINAMP_PAUSE whatever)
                                                :Normal setup:
                                                                                girder-internet-event-client %MUSICSERVERIPONLY %GIRDERPORT %GIRDERPASSWORD WINAMP_PAUSE whatever
                                                if "%DEBUGGIRDER%" eq "1" (echo girder-internet-event-client %MUSICSERVERIPONLY %GIRDERPORT %GIRDERPASSWORD WINAMP_PAUSE whatever)
                                                call debug "(If that didn't work, try 'paus' without the 2 after it to do it with WAWI instead of Girder.)"
                                                set UNDOCOMMAND=unpause
                                                set REDOCOMMAND=pause.btm %*
                                            goto :END


:END
:DoNothing
    call get-winamp-state
    :END_Quickly
    if "%1" eq "exitafter" .or. "%2" eq "exitafter" (exit)

