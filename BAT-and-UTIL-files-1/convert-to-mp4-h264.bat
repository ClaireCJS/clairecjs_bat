@Echo OFF
 on break cancel

set              REDOCOMMAND=ffmpeg -i "%@UNQUOTE[%1]" -vcodec libx264 "%@UNQUOTE[%@NAME[%1].mp4]"
call print-if-debug %REDOCOMMAND%
                %REDOCOMMAND%

