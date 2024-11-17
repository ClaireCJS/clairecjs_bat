@Echo OFF

set              REDOCOMMAND=ffmpeg -i "%@UNQUOTE[%1]" -vcodec copy -acodec copy "%@UNQUOTE[%@NAME[%1].mp4]"
call print-if-debug %REDOCOMMAND%
                %REDOCOMMAND%

