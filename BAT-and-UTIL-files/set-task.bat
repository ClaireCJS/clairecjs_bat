@Echo OFF
:USAGE: call set-task "downloading youtube albums"

set TASK=%@UNQUOTE[%1]
call set-window-title "%TASK%"

