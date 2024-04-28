@Echo OFF

:USAGE: "Divider"      to draw a horizontal divider using the default character repeated
:USAGE: "Divider -"    to draw a horizontal divider using the   '-'   character repeated
:USAGE: "Divider 😂"   to draw a horizontal divider using the laugh-emoji (😂)  repeated
:USAGE: "Divider HII!" to draw a horizontal divider using the string  "HII!"    repeated 
:USAGE: OPTION:        Add "big" as a 2nd parameter to use double-height text

rem CONFIGURATION:
        call turn-off-file-redirection
        set DEFAULT_DIVIDER==
        rem                 ^ our default divider is '=', the equal symbol


rem Respond to parameters [if any]:
        set DIVIDER_PARAM1=%1
        if defined USE_THIS_DIVIDER (
            set DIVIDER_PARAM1=%USE_THIS_DIVIDER%
            unset /q USE_THIS_DIVIDER
        )

                                                                       set DIVIDER=%DEFAULT_DIVIDER%
        if "%DIVIDER_PARAM1%" ne "" .and. "%DIVIDER_PARAM1%" ne "big" (set DIVIDER=%@UNQUOTE[%DIVIDER_PARAM1%])
                                                           set BIG=0
        if "%2" eq "big" .or. "%DIVIDER_PARAM1%" eq "big" (set BIG=1)


rem Our divider could be any length, and our screen could have any number of columns,
rem so we must determine how many times we must repeat our divider to fill the line,
rem all while considering that double-height lines use 2 columns per character:
                      set SCREEN_COLUMNS=%_COLUMNS
        if %BIG eq 1 (set SCREEN_COLUMNS=%@EVAL[%SCREEN_COLUMNS / 2])
        set DIVIDER_LENGTH=%@LEN[%DIVIDER]
        set NUM_REPEATS=%@EVAL[%SCREEN_COLUMNS / %DIVIDER_LENGTH]

rem Actually write out the divider, which is easy for normal height text:
        if %BIG ne 1 (repeat %NUM_REPEATS% echos %DIVIDER% %+ goto :END)

rem But a bit more complicated for double-height text, particulary when dealing with a 
rem TCC/Windows Terminal rendering bug that required a lot of ANSI fuddling to deal with...
        set DIVIDER_FULL=%DIVIDER%
        set NUM_REPEATS=%@EVAL[%NUM_REPEATS - 1]
        repeat %NUM_REPEATS set DIVIDER_FULL=%DIVIDER%%DIVIDER_FULL%
        rem works but blank line necessary after because that one line is stuck in big:
        echo %ANSI_SAVE_POSITION%%BIG_TOP%%DIVIDER_FULL%%ANSI_RESTORE_POSITION%%BIG_OFF%%NEWLINE%%@ANSI_MOVE_UP[1]%BIG_BOT%%DIVIDER_FULL%

        rem echos %ANSI_SAVE_POSITION%
        rem echos %BIG_TOP%%DIVIDER_FULL%%BIG_OFF%
        rem echos %ANSI_RESTORE_POSITION%
        rem echos %NEWLINE%%@ANSI_MOVE_UP[1]%@ANSI_MOVE_TO_COL[1]
        rem rem echos %ANSI_SAVE_POSITION%
        rem echos %BIG_BOT%%DIVIDER_FULL%
        rem echos %BIG_OFF%
        rem echos %ANSI_RESTORE_POSITION%%NEWLINE%%BIG_OFF%%@ANSI_MOVE_UP[1]
        rem echos %BIG_OFF%%ANSI_ERASE_CURRENT_LINE%%BIG_OFF%
        rem echos %ANSI_RESTORE_POSITION%
        rem echos %BIG_OFF%%@ANSI_MOVE_UP[1]%BIG_OFF%%ANSI_ERASE_CURRENT_LINE%%BIG_OFF%%@ANSI_MOVE_TO_COL[1]%BIG_OFF%
        rem echos %NEWLINE%%BIG_OFF%%ANSI_RESET%%NEWLINE%helloooooooooooooo%@ANSI_MOVE_UP[1]Y%@ANSI_MOVE_UP[1]Z
        rem echos %newline%
        rem echo.


:END

call turn-on-file-redirection


