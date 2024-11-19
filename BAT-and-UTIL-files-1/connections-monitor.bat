@echo off
 on break cancel
 cls %+ echo.

set HEADER=%ANSI_COLOR_IMPORTANT%%EMOJI_LAPTOP%%EMOJI_GLOBE_WITH_MERIDIANS% %FAINT_ON%%ITALICS_ON%Connections:%FAINT_OFF%%ITALICS_OFF% ``

set POSITION_RESET=%ANSI_SHOW_CURSOR%%@ANSI_MOVE_UP[]%@ANSI_MOVE_UP[]%@ANSI_MOVE_TO_COL[1]

:Again
    set connections=%@EXECSTR[(netstat |:u8 wc -l) >&>nul]
    echo %POSITION_RESET%%HEADER%%BIG_TOP%%@RAND_FG[]%CONNECTIONS%   ``
    echos %HEADER%%BIG_BOT%%@RAND_FG[]%CONNECTIONS%   %ANSI_HIDE_CURSOR%``
    delay /M 500
goto :Again

echos %ANSI_SHOW_CURSOR%                %+ rem Just in case


