@Echo off

::::: PURPOSE:  To echo all eoji variables representing a regular expression we provide


REM parameter processing
        set PARAM=%1
        set SILENT=0
        if "%PARAM%" eq  ""  (set PARAM=.*)
        if  "silent" eq "%1" (set SILENT=1)


REM dump environment to file
        if not defined TMPFILE (call settmpfile)
        if not exist %TMPFILE% .or. "%2" eq "force" (
            call important "Dumping environment variables..."
            timer /4 on
            REM 2.2 seconds            set|sed "s/=.*$//ig" >"%TMPFILE%"
            set|cut -d "=" -f1 >"%TMPFILE%"
            timer /4 off
            :DEBUG: (set|sed "s/=.*$//ig") %+ echo TMPFILE: %+ type "%TMPFILE%" %+ pause
        )

REM go through each enviroment variable
        for /f "tokens=1-999" %co in (%TMPFILE%) gosub ProcessEnvVar %co%


goto :END
    :ProcessEnvVar [var]
        if          "%@REGEX[EMOJI_,%@UPPER[%VAR%]]" ne "1" (return)
        if "%@REGEX[%@UPPER[%PARAM],%@UPPER[%VAR%]]" ne "1" (return)
        if %FOUND ne 1 (echo.)
        set FOUND=1
        if %SILENT ne 1 (
            echo  %faint%* This is%faint_off% %VAR%: %[%VAR%]
            REM also echo it in double-height if we can:
                if defined BIG_TOP .and. defined BIG_BOT (
                    echo   %BIG_TOP%%[%VAR%]
                    echo   %BIG_BOT%%[%VAR%]
                )
            echo.
        )
    return
:END
