@on break cancel
@Echo off

:DESCRIPTION:  To search emoji environment variables (set by set-emoji.bat) using a regular expression [i.e. "grep my emojis"]
:REQUIRES: set-emoji.bat (to set emoji envirionment variables), emoji.env (used by set-emoji.bat), print-message.bat, set-tmp-file.bat, important.bat, set-colors.bat (to set color environment variables)

REM parameter processing
        set PARAM=%1
        set SILENT=0
        if "%PARAM%" eq  ""  (set PARAM=.*)
        if  "silent" eq "%1" (set SILENT=1)
        call validate-environment-variables STAR PARAM BIG_TOP BIG_BOT

REM dump environment to tmp%file
        call dump-environment-to-tmpfile.bat %+ rem sets env_dump_tmpfile
        call validate-environment-variable env_dump_tmpfile "something went wrong with dump-environment-to-tmpfile.bat"

REM go through each enviroment variable
        echo.
        set EMOJI_GREP_RESULTS=
        for /f "tokens=1-999" %co in (%env_dump_tmpfile%) gosub ProcessEnvVar %co%

        iF "%EMOJI_GREP_RESULTS%" eq "" (
            call warning "Found no emoji with '%italics%%PARAM%%italics_off%' in its name"
        ) else (
            echo.
            echo  %star% These are all the results: %EMOJI_GREP_RESULTS%
            echo.
            call bigecho %EMOJI_GREP_RESULTS%
        )

goto :END
    :ProcessEnvVar [var]
        if          "%@REGEX[EMOJI_,%@UPPER[%VAR%]]" ne "1" (return)
        if "%@REGEX[%@UPPER[%PARAM],%@UPPER[%VAR%]]" ne "1" (return)
        if %FOUND ne 1 (echo.)
        set FOUND=1
        set EMOJI_GREP_RESULTS=%EMOJI_GREP_RESULTS% %[%VAR%]
        if %SILENT ne 1 (
            echo  %faint%%star% This is%faint_off% %VAR%: %[%VAR%]
            REM also echo it in double-height if we can:
                if defined BIG_TOP .and. defined BIG_BOT (
                    echo   %BIG_TOP%%[%VAR%]
                    echo   %BIG_BOT%%[%VAR%]
                )
            echo.
        )
    return
:END
