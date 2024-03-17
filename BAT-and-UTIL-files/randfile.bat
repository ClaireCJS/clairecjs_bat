@Echo off

if "%1" eq "legacy" goto :legacy

:2023
        rem validate environment/setup
            call validate-in-path set-randomfile success advice cl 

        rem folder-specific behaviors:
            set MASK=
            set RANDOMLY_WATCHING_VIDEOS=0
            if "%_CWP" eq "\MEDIA\FOR-REVIEW\DO_LATERRRRRRRRRRRRRRRRRRRRRRR\oh" (
                set RANDOMLY_WATCHING_VIDEOS=1
                call validate-environment-variable FILEMASK_VIDEO
                set MASK=%FILEMASK_VIDEO%
            )
            if "%1" ne "" (set MASK=%1)

        rem Determine our random filename:
            call set-randomfile %MASK%

        rem Let user know:
            echo.
            echo %ANSI_COLOR_SUCCESS%%CHECK%%CHECK%%CHECK% Random file is:
            echo. %+ %color_important_less% %+ echo       "%random_file%"
            echo. %+ %color_important%      %+ echo       "%random_file_filename_only%"
            echo.
            call advice "Filename is copied to clipboard {with quotes}"
            call cl "%random_file_filename_only%"

        rem More folder-based behavior:
            if %RANDOMLY_WATCHING_VIDEOS eq 1 (keystack "watch " ctrl-v)

goto :END


:legacy
            set PARAMS=%*
            if "%PARAMS%" eq "legacy" set PARAMS=
            call fixtmp
            set randfile=%@EXECSTR[dir /ba:-d %PARAMS%|randline]
            if not exist "%randfile" goto :nofile
            call cl %randfile
            echo "%randfile"
            call unimportant "Filename without quotes copied to clipboard!"
            keystack "%randfile"
            REM why would we not leae this to be used later? unset /q randfile
            goto :END
            :nofile
            call warning "Sorry, no files here!"
            goto :END


:END
