@Echo off


:DESCRIPTION: Gets the current state of the music, and sets MUSICSTATE to one of the following values:
:DESCRIPTION:         PAUSED
:DESCRIPTION:         STOPPED
:DESCRIPTION:         PLAYING
:                     
:USAGE: get-winamp-state [silent]
:                     
:REQUIRES: 1) WinAmp with the WAWI plugin installed       
:REQUIRES: 2) MUSICSERVERSTATUSURL MUSICSERVERMACHINENAME MACHINENAME environments variable set to music server (including port) for example "68.167.161.182:666"
:REQUIRES: 3) OLD REQUIREMENT: Perl with LWP::Simple (to run winamp-status.pl) [BUT THIS BROKE IN 2016; NOW USING WGET)
                     
                     

::::: VALIDATE ENVIRONMENT:
    if "%VALIDATED_GET_WINAMP_STATE%" eq "1" goto :EnvironmentAlreadyValidated
            call validate-environment-variables MUSICSERVERSTATUSURL MUSICSERVERMACHINENAME MACHINENAME
            call validate-in-path               winamp-status-from-file.pl warning isRunning wget.exe
            set VALIDATED_GET_WINAMP_STATE=1
    :EnvironmentAlreadyValidated

::::: INITIALIZE VALUES:
    set SKIP_CHECKING_IF_IT_IS_RUNNING_BUT_ONLY_IF_ON_THE_ESRVER_ITSELF=1
    set ISRUNNING=1 
    SET MUSICSTATE=UNKNOWN


::::: GET PARAMETERS:
    set PARAM=%1
                             set SILENT=0
    if "%PARAM%" eq "silent" set SILENT=1

::::: CHECK IF IT IS RUNNING (BUT ONLY IF IT'S ON THE SAME MACHINE) PRIOR TO ATTEMPT -- but why? This is slow?
    if "%SKIP_CHECKING_IF_IT_IS_RUNNING_BUT_ONLY_IF_ON_THE_ESRVER_ITSELF" eq "1" goto :Nevermind_1
        if "%MACHINENAME%" eq "%MUSICSERVERMACHINENAME%" (call isRunning WinAmp)
    :Nevermind_1

::::: FETCH WINAMP STATE IF APPLICABLE:
    if %ISRUNNING eq 0 (goto :IsNotRunning)
        ::OLD METHOD relies on unreliable LWP::Simple: set MUSICSTATE=%@EXECSTR[winamp-status-from-file.pl]
        ::NEW METHOD relies on external wget:
        rem                     WGETDIR=c:\logs\wget
        set                     WGETDIR=%TMP%
        set       WGETFILEBASE=main.%_DATETIME.%_PID
        set           WGETFILE=%WGETDIR%\%WGETFILEBASE%
        if exist    "%WGETFILE%"       (*del /qy "%WGETFILE%" >nul)
        rem wget.exe --quiet -t 2 -P %WGETDIR% %MUSICSERVERSTATUSURL%
            wget.exe --quiet -t 2 -P %WGETDIR% -O %WGETFILE% %MUSICSERVERSTATUSURL%
        rem set       WGET_RETURN_FILE=%WGETDIR%\main
        set           WGET_RETURN_FILE=%WGETFILE%
        if not exist %WGET_RETURN_FILE% (call warning "WinAmp may not be running, or WAWI may not be installed, because WGET_RETURN_FILE of '%WGET_RETURN_FILE%' does not exist")

        if "%1" eq "fast" (goto :Fast  )
        if "%1" ne "fast" (goto :normal)
                REM this experimental fast mode did nothing to speed things up, not really any faster than calling the perl script
                :fast
                    setdos /x-126
                        DO line IN @%WGET_RETURN_FILE (
                            REM echo "%ANSI_MAGENTA%line is '%line'"
                            if "%line" ne "" (
                                if    "%@REGEX[Playing track,%line]" eq "1" (set MUSICSTATE=PLAYING)
                                if  "%@REGEX[Paused in track,%line]" eq "1" (set MUSICSTATE=PAUSED)
                                if "%@REGEX[Stopped at track,%line]" eq "1" (set MUSICSTATE=STOPPED)
                            )
                        )
                    setdos /x0
                goto :normal_done
                :normal
                        if not exist %WGET_RETURN_FILE (set MUSICSTATE=UNKNOWN)
                        if     exist %WGET_RETURN_FILE (set MUSICSTATE=%@EXECSTR[winamp-status-from-file.pl <%WGET_RETURN_FILE%])
                :normal_done

    :IsNotRunning

::::: EMOJIFY & COLOR-CODE THE RESPONSES:
    if "%MUSICSTATE%" eq "PAUSED"  (color bright yellow on black %+ set MUSIC_EMOJI=%EMOJI_PAUSE_BUTTON %+ set MUSIC_ANSI=%ANSI_BRIGHT_YELLOW)
    if "%MUSICSTATE%" eq "STOPPED" (color bright red    on black %+ set MUSIC_EMOJI=%EMOJI_STOP_BUTTON  %+ set MUSIC_ANSI=%ANSI_BRIGHT_RED   )
    if "%MUSICSTATE%" eq "PLAYING" (color bright green  on black %+ set MUSIC_EMOJI=%EMOJI_PLAY_BUTTON  %+ set MUSIC_ANSI=%ANSI_BRIGHT_GREEN )

::::: REPORT THE STATE (if not in silent mode):
    if %SILENT ne 1 (%COLOR_DEBUG% %+ echos %MUSIC_EMOJI% music state is %MUSIC_ANSI%%italics%%MUSICSTATE%%italics_off%%BOLD_OFF%%ANSI_RESET% %ANSI_COLOR_DEBUG%%MUSIC_EMOJI% %+ %COLOR_NORMAL% %+ echo.)

::::: COPY THE STATE TO ALIAS VARIABLES:
    set MUSIC_STATE=%MUSICSTATE%
    set WINAMP_STATE=%MUSICSTATE%
