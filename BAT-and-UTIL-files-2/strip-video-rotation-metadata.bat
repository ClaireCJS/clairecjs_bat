@Echo OFF
@on break cancel

::::: VALIDATE PARAMETERS:
    if  ""  eq   "%1" (gosub :NoArg "first"     %+ goto :END)
    :f  ""  eq   "%2" (gosub :NoArg "second"    %+ goto :END)
    if not exist "%1" (gosub :DNE   "first"  %1 %+ goto :END)
    :f not exist "%2" (gosub :DNE   "second" %2 %+ goto :END)
    set INPUT=%1
    set OUTPUT=%@NAME[%INPUT%] (rotation metadata removed).%@EXT[%INPUT%]

::::: MAIN:
    :           :0=90CounterCLockwise and Vertical Flip  (default) 
    :           :1=90Clockwise 
    :           :2=90CounterClockwise 
    :           :3=90Clockwise and Vertical Flip
    :et LAST_FFMPEG_COMMAND=call ffmpeg -i %@SFN["%INPUT%"] -vf "rotate=PI/2"                                        "%OUTPUT%" %+ REM rotated video AND metadata and makes HTML5 embed fail wtf
    :et LAST_FFMPEG_COMMAND=call ffmpeg -i %@SFN["%INPUT%"] -vf "transpose=1"                                        "%OUTPUT%" %+ REM HTML5 embed fails for all of them, actually
    :et LAST_FFMPEG_COMMAND=call ffmpeg -i %@SFN["%INPUT%"] -vf "transpose=1" -metadata:s:v rotate="90"              "%OUTPUT%" %+ REM 
    :et LAST_FFMPEG_COMMAND=call ffmpeg -i %@SFN["%INPUT%"] -metadata:s:v "rotate=0" -vf "transpose=1" -codec:a copy "%OUTPUT%" %+ REM 
    :et LAST_FFMPEG_COMMAND=call ffmpeg -i %@SFN["%INPUT%"] -metadata:s:v "rotate=0" -vf "rotate=90"   -codec:a copy "%OUTPUT%" %+ REM a fucking trapezoid what the fuck
    set LAST_FFMPEG_COMMAND=call ffmpeg -i %@SFN["%INPUT%"] -metadata:s:v "rotate=0"                   -codec:a copy "%OUTPUT%" %+ REM  SUCCESS! But this is really stripping...

    %COLOR_RUN% %+ %LAST_FFMPEG_COMMAND%

::::: CLEANUP:
    call deprecate %1
    :: if not isdir "rotated" md "rotated"
    :: mv %1*deprecated "rotated"

goto :END
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :Usage
            %COLOR_IMPORTANT% 
            echo. %+ echo.
            echo  USAGE: %0 [file1] [file2]
            echo.
            echo            Rotates a video 90 degrees clockwise.
            echo            http://stackoverflow.com/questions/3937387/rotating-videos-with-ffmpeg
            echo.
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :NoArg [desc]
            echo. %+ echo. %+ 
            %COLOR_ALARM%  %+ echos FATAL ERROR: %desc% argument cannot be blank!
            %COLOR_NORMAL% %+ echo.
            gosub :Usage
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :DNE [desc val]
            echo. %+ echo. %+ 
            %COLOR_ALARM%  %+ echos FATAL ERROR: %desc% argument of %val% DOES NOT EXIST!
            %COLOR_NORMAL% %+ echo.
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:END


:Audit
    set LAST_FILE_ROTATED_INPUT=%1
    set LAST_FILE_ROTATED_OUTPUT=%2
:Cleanup
    %COLOR_NORMAL%


