@Echo off
REM sleep 1
set MYCOLOR=%@ANSI_BG[40,0,0]
set MYCOLOR=
set MYCOLOR=%@ANSI_BG[40,0,0]%@ANSI_FG[255,48,48]
:et  askyn_decorator=%ANSI_COLOR_PROMPT%%BLINK%
set  askyn_decorator=
set  prev_title=%_wintitle

rem some weird bug where we need to move left 1 more column than expected when counting down [probably due to ansi weirdness], 
rem otherwise a bit of screen junk remains, so we set LEFT_MORE=1 to kludge askyn.bat:
        set LEFT_MORE=1
        rem came here thinking there was a bug in askyn but it turned out it was just the 'no_enter' option here deliberately making enter not work... 😂 2024/09/08
        call askyn "%MYCOLOR%%italics%%blink%%underline%Return%underline_off% to command line?%blink_off%%italics_off" yes 99999 no_enter big
        set LEFT_MORE=0

title %prev_title%

if "%DO_IT%" ne 1 goto :END
rem iff %DO_IT eq 1 then

        title %prev_title% 
        pause 
        set FORCE_EXIT=1 
        echo %ANSI_COLOR_RED%—— Returning to command line #1 of 2 ——%ANSI_COLOR_NORMAL%
        rem not *CANCELing anymore but calling BAT 
        call cancelll.bat
        *cancel
rem endiff

rem if %DO_IT eq 1 (
    echo %ANSI_COLOR_RED%—— Returning to command line #2 of 2 ——%ANSI_COLOR_NORMAL%
    rem *CANCEL
    rem not *CANCELing anymore but calling BAT 
    call cancelll.bat
    *cancel
rem ) %+ rem Redundant double-cancel just-in-case {having some suspicious behavior as of 2024/10, bug reported 2022/11/10}


:END
if 1 eq %DO_IT (*CANCEL)