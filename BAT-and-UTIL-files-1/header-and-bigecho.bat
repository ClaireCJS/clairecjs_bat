@on break cancel
@Echo OFF
set  HABPARAMS=%STAR% %@UNQUOTE[%*]
set  header_noecho=1
call header  "%HABPARAMS%"
set  header_noecho=0
echo.
echos %@ANSI_MOVE_UP[1]%@ANSI_MOVE_TO_COL[1]%BIG_OFF%%ANSI_ERASE_TO_EOL%%ANSI_RESET%%BIG_OFF%
call bigecho "%HABPARAMS%"
