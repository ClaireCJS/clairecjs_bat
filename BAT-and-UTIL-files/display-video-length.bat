@Echo OFF



::::: VALIDATE PARAMETERS:
    if "%1" eq ""                 (gosub :Usage                    %+ goto :END)
    if not exist "%1"             (gosub :DNE  "first argument" %1 %+ goto :END)


::::: MAIN:
    ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 %1

goto :END
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Usage
            %COLOR_IMPORTANT% %+ echo. %+ echo.
            echo  USAGE: %0 [file1]
            echo.
            echo            Echos the length of a video, in seconds, to STDOUT.
            echo.
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :DNE [desc val]
            call fatal_error "DOES NOT EXIST: %desc% of %val% "
        return
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:END


:Audit
    set LAST_FILE_PROBED_FOR_VIDEO_LENGTH=%1
:Cleanup
    %COLOR_NORMAL%


