@loadbtm on
@on break cancel
@Echo off

:USAGE: isRunning {regex} ['quiet'] - sets envvar ISRUNNING to 0 or 1, depending on if a process matching regex is running
:USAGE:                               optional param 2 of 'quiet' makes it silent mode
:USAGE: SET ISRUNNING_FAST=1 to run it at a faster speed, but can only check PID

rem DEBUG:
	if %DEBUG eq 1 (Echo ON)


rem Validate environment:
        iff "1" != "%validated_isrunning%" then
                call validate-in-path               isrunning-helper debug grep type 
                call validate-environment-variables ansi_colors_have_been_set emoji_have_been_set
                set  validated_isrunning=1
        endiff


rem CHECK IF THE PROCESS IS RUNNING:
    unset /q OUTPUT
    if "1" == "%isRunning_fast%" (
        set COMMENTISRUNNING=echo doing fast, %%1='%1'
        iff %@pid[%1] ne 0 then
            set ISRUNNING=1
        else
            set ISRUNNING=0
        endiff
    ) else (
        set COMMENTISRUNNING=had to remove these in 2022 when moving to Windows 10... set TASKLIST_NONEXE_OPTIONS=/l /o
        REM old command was: set OUTPUT=%@EXECSTR[taskList  %*|grep -i -v grep|grep -i -v keep-killing-if-running|grep -i -v react-after-program-closes] ADFASDFASFDASDF
        set  OUTPUT=%@EXECSTR[isRunning-helper %*]
        if %DEBUG eq 1 (call debug "%OUTPUT is '%italics%%OUTPUT%%italics_off%'")
        if "%OUTPUT%" == "" (set ISRUNNING=0)
        if "%OUTPUT%" != "" (set ISRUNNING=1)
    )



rem INFORM USER:
	if "%ISRUNNING%" == "1" goto :IsRunning_YES
                                goto :IsRunning_NO

            :IsRunning_YES
                    set emoji=%EMOJI_CHECK_MARK
                    color green on black     
                    rem echos %@ANSI_RGB_BG[0,60,0]
                    iff "%2" == "quiet" .or. "%2" == "silent" then
                            rem (do nothing)
                    else
                            @echos %emoji% %italics%%1%italics_off% %underline%is%underline_off% running %emoji%``     
                            %COLOR_NORMAL% 
                            echo. 
                    endiff
                    set LAST_ISRUNNING=1 %+ 
            goto :IsRunning_END

            :IsRunning_NO
                    color bright red on blue 
                    echos %@ANSI_RGB_BG[80,0,0]
                            if "%2" == "quiet" .or. "%2" == "silent" (goto :Quiet_YES)
                                    :Quiet_No
                                            iff 1 eq %SLEEPING% then
                                                    @echos . %+ %COLOR_NORMAL% 
                                            else
                                                    @echos %emoji_stop_sign% %italics%%1%italics_off% is %double_underline%NOT%double_underline_off% running %emoji_stop_sign%`` %+ %COLOR_NORMAL% %+ echo.
                                            endiff
                                            goto :Quiet_DONE
                                    :Quiet_YES
                                     goto :Quiet_DONE
                            :Quiet_DONE
                    set LAST_ISRUNNING=0
            goto :IsRunning_END

    :IsRunning_END
    %COLOR_NORMAL%


rem ALIASES:
    set IS_RUNNING=%ISRUNNING%
    set LASTISRUNNING=%LAST_ISRUNNING%
