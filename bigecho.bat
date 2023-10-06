@echo off

:USAGE: optionally set COLOR_TO_USE=<command to set the color to use> prior to calling for cosmetically better background color handling to avoid the cosmetic weirdness of newlines with a different background color


if not defined BIG_TEXT_LINE_1 (call error "BIG_TEXT_LINE_1 is not defined. Try running set-colors.bat")
if not defined BIG_TEXT_LINE_2 (call error "BIG_TEXT_LINE_2 is not defined. Try running set-colors.bat")


set PARAMS=%@UNQUOTE[%*]

setdos /x-678

    %COLOR_TO_USE% %+ echos %BIG_TEXT_LINE_1%%PARAMS%%BIG_TEXT_END% %+ %COLOR_NORMAL% %+ echo.
    %COLOR_TO_USE% %+ echos %BIG_TEXT_LINE_2%%PARAMS%%BIG_TEXT_END% %+ %COLOR_NORMAL% %+ if %ECHOSBIG ne 1 (echo.)

    echos %BIG_TEXT_END%%ANSI_RESET%


setdos /x0

REM option should only affect it once
if defined COLOR_TO_USE (set COLOR_TO_USE=)

