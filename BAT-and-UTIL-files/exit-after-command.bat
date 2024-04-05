@Echo OFF

:DESCRIPTION: For running a command and exiting after



::::: OPTIONS:
    if "%WINDOW_MINIMIZE%" eq  "1" (window min )
    if  "WINDOW_MINIMIZE"  eq "%1" (window min )
    if "%WINDOW_HIDE%"     eq  "1" (window hide)
    if  "WINDOW_HIDE"      eq "%1" (window hide)




::::: PASS THORUGH THE COMMAND-LINE:
%*



unset /q WINDOW_MINIMIZE
unset /q WINDOW_HIDE

exit



