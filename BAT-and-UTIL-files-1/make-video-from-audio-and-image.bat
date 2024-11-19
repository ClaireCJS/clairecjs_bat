@on break cancel
@Echo off




%COLOR_WARNING% %+ echo -- NOTE: Image must have width divisible by 2. %+ %COLOR_NORMAL%




if "%1" eq "" .or. "%2" eq "" (gosub USAGE        %+ goto :END)
if not exist %1               (gosub DNE "1st" %1 %+ goto :END)
if not exist %2               (gosub DNE "2nd" %2 %+ goto :END)

set AUDIO=%1
set IMAGE=%2

%COLOR_DEBUG% %+ echo ffmpeg -loop 1 -i %IMAGE% -i %AUDIO% -c:v libx264 -tune stillimage -c:a aac -strict experimental -b:a 192k -pix_fmt yuv420p -shortest  "%@UNQUOTE[%@NAME[%AUDIO].mp4]"
                      ffmpeg -loop 1 -i %IMAGE% -i %AUDIO% -c:v libx264 -tune stillimage -c:a aac -strict experimental -b:a 192k -pix_fmt yuv420p -shortest  "%@UNQUOTE[%@NAME[%AUDIO].mp4]"

call rnlatest

goto :END

        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :USAGE
            %COLOR_ADVICE%
            echo USAGE: %0 {audio-filename} {image-filename,image must not have odd width or height} 
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :DNE [desc val]
            %COLOR_ALARM%
            echo FATAL ERROR: %desc% argument is a file that does not exist: %val%
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END