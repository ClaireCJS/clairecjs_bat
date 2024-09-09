@Echo off
REM sleep 1
set MYCOLOR=%@ANSI_BG[40,0,0]
set MYCOLOR=
set MYCOLOR=%@ANSI_BG[40,0,0]%@ANSI_FG[255,48,48]
:et  askyn_decorator=%ANSI_COLOR_PROMPT%%BLINK%
set  askyn_decorator=
:all askyn "%DOUBLE_UNDERLINE%%MYCOLOR%Cancel%DOUBLE_UNDERLINE_OFF% %bold%all%bold_off% execution %italics_off%and%italics_on% %underline%return%underline_off% to command line?" yes 999999 no_enter big

rem some weird bug where we need to move left 1 more column than expected when counting down [probably due to ansi weirdness], 
rem otherwise a bit of screen junk remains, so we set LEFT_MORE=1 to kludge askyn.bat:
    set LEFT_MORE=1
    rem came here thinking there was a bug in askyn but it turned out it was just the 'no_enter' option here deliberately making enter not work... 😂 2024/09/08
    call askyn "%MYCOLOR%%italics%%blink%%underline%Return%underline_off% to command line?%blink_off%%italics_off" yes 99999 no_enter big
    set LEFT_MORE=0

if %DO_IT eq 1 (CANCEL)

