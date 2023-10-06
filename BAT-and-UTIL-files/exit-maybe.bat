@Echo off
REM sleep 1
set MYCOLOR=%@ANSI_BG[40,0,0]
set MYCOLOR=
set MYCOLOR=%@ANSI_BG[40,0,0]%@ANSI_FG[255,48,48]
:et  askyn_decorator=%ANSI_COLOR_PROMPT%%BLINK%
set  askyn_decorator=
:all askyn "%DOUBLE_UNDERLINE%%MYCOLOR%Cancel%DOUBLE_UNDERLINE_OFF% %bold%all%bold_off% execution %italics_off%and%italics_on% %underline%return%underline_off% to command line?" yes 999999 no_enter big
call askyn "%MYCOLOR%%italics%%blink%%underline%Return%underline_off% to command line?%blink_off%%italics_off" yes 999999 no_enter big
if %DO_IT eq 1 (CANCEL)

