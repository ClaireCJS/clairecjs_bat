@Echo Off

::::: USAGE: 
	:isRunning winamp - sets envvar ISRUNNING to 0 or 1, depending on if winamp (in this example) is running

::::: DEBUG:
	if %DEBUG eq 1 (Echo ON)

::::: SETUP:
    REM 20230714 not sure why running this so removing for speedup: call fixtmp





::::: CHECK IF THE PROCESS IS RUNNING:
    if %isRunning_fast eq 1 (
        set COMMENTISRUNNING=echo doing fast, %%1='%1'
        if %@pid[%1] ne 0 (
            set ISRUNNING=1
        ) else (
            set ISRUNNING=0
        )
    ) else (
        set COMMENTISRUNNING=had to remove these in 2022 when moving to Windows 10... set TASKLIST_NONEXE_OPTIONS=/l /o
        REM old command was: set OUTPUT=%@EXECSTR[taskList  %*|grep -i -v grep|grep -i -v keep-killing-if-running|grep -i -v react-after-program-closes] ADFASDFASFDASDF
        set  OUTPUT=%@EXECSTR[isRunning-helper %*]
        if %DEBUG eq 1 (echo %ANSI_COLOR_DEBUG%OUTPUT is '%italics%%OUTPUT%%italics_off%')
        if "%OUTPUT%" eq "" (set ISRUNNING=0)
        if "%OUTPUT%" ne "" (set ISRUNNING=1)
    )



::::: INFORM USER:
	if "%ISRUNNING%" eq "1" goto :IsRunning_YES
                            goto :IsRunning_NO
            :IsRunning_YES
                set emoji=%EMOJI_CHECK_MARK
                color green on black     
                echos %@ANSI_RGB_BG[0,60,0]
                @echos %emoji% %italics%%1%italics_off% %underline%is%underline_off% running %emoji%``     
                %COLOR_NORMAL% 
                echo. 
                set LAST_ISRUNNING=1 %+ 
            goto :IsRunning_END
            :IsRunning_NO
                color bright red on blue 
                echos %@ANSI_RGB_BG[80,0,0]
                    if "%2" eq "quiet" goto :Quiet_YES
                            :Quiet_No
                                @echos %emoji_stop_sign% %italics%%1%italics_off% is %double_underline%NOT%double_underline_off% running %emoji_stop_sign%`` %+ %COLOR_NORMAL% %+ echo.
                                goto :Quiet_DONE
                            :Quiet_YES
                                @echos . %+ %COLOR_NORMAL% 
                                goto :Quiet_DONE
                        :Quiet_DONE
                set LAST_ISRUNNING=0
            goto :IsRunning_END
    :IsRunning_END
    %COLOR_NORMAL%


::::: ALIASES:
    set IS_RUNNING=%ISRUNNING%
    set LASTISRUNNING=%LAST_ISRUNNING%
