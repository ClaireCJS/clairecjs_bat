@echo off
 on break cancel
%COLOR_SUBTLE%
    if     defined WGET_DECORATOR            echos %WGET_DECORATOR
    if     defined WGET_DECORATOR_ON         echos %WGET_DECORATOR_ON
    if not defined WGET_DECORATOR .and. not defined WGET_DECORATOR_ON echos %FAINT_ON%%overstrike_on%
                   wget32.exe %*
    if not defined WGET_DECORATOR_OFF                                 echos %FAINT_Off%%overstrike_off%
    if     defined WGET_DECORATOR_OFF        echos %WGET_DECORATOR_OFF
%COLOR_NORMAL%