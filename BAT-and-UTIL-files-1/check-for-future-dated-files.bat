@echo off
@loadbtm on
@on break cancel


rem HELP:
        iff "%1" == "/?" .or. "%1" == "?" .or. "%1" == "/h" .or. "%1" == "-h" .or. "%1" == "--help" .or. "%1" == "/help" then
                echo.
                echo USAGE: check-for-future-dated-files     -- default invocation
                echo USAGE: check-for-future-dated-files /t  -- touch future-dated files so that they are no longer dated in the future
                echo.
                echo * This script checks for future-dated files and stores result in %%FUTURE_DATED_FILES_EXIST%% (1==they exist, 2==do not)
                echo * If the /t option is given, it calls the touch utility to change the file’s date to the present
                goto /i :END
        endiff


rem Validate environment:
        iff "%1" != "/t" then
                set TOUCHA_TOUCHA=0
        ELSE
                set TOUCHA_TOUCHA=1
                iff "1" != "%validated_checkforfuturefiles_t%" then
                        call validate-in-path touch
                        set validated_checkforfuturefiles_t=1
                endiff
        endiff

rem CYCLE THROUGH EACH FILE:
        set FILES_TO_CHECK=*
        set FUTURE_DATED_FILES_EXIST=0
        for /a: /h %tmpCurrentFile in (%FILES_TO_CHECK%) gosub ProcessFile "%tmpCurrentFile%"



rem ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
        goto :end
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :ProcessFile [file]
                rem %COLOR_IMPORTANT% %+ echo %ansi_color_important%- Processing file: “%ansi_color_important_less%%file%%ansi_color_important%”%ansi_color_normal%
                set file2=%@UNQUOTE[%file%]
                set age_now=%@makeage[%_date,%_time] 
                set age_file=%@fileage[%file%]
                set age_diff=%@EVAL[%age_now% - %age_file%]
                rem DEBUG: echo now = %age_now% / file = %age_file% / diff = %age_diff / name=%file%
                iff %age_diff% lt 0 then
                        if "1" != "%FUTURE_DATED_FILES_EXIST%" echo.
                        echo %ansi_color_warning% %EMOJI_WARNING% FUTURE-DATED FILE DETECTED: %file2% %emoji_warning% %ansi_color_normal%
                        set FUTURE_DATED_FILES_EXIST=1
                        iff "1" == "%TOUCHA_TOUCHA%" then
                                echo %ansi_color_warning% %EMOJI_WARNING% Touching file to update to current date! %emoji_warning% %ansi_color_normal%
                                touch %file%
                        endiff
                endiff
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
rem ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════



:END
