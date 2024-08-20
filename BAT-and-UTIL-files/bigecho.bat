@echo off

:USAGE: optionally set COLOR_TO_USE=<command to set the color to use> prior to calling for cosmetically better background color handling to avoid the cosmetic weirdness of newlines with a different background color


rem Validate environment
        if %BIGECHO_VALIDATED ne 1 (
            if not defined BIG_TEXT_LINE_1 (call error "BIG_TEXT_LINE_1 is not defined. Try running set-colors.bat")
            if not defined BIG_TEXT_LINE_2 (call error "BIG_TEXT_LINE_2 is not defined. Try running set-colors.bat")
            call validate-environment-variables BIG_TEXT_LINE_1 BIG_TEXT_LINE_2 BIG_TEXT_END ANSI_RESET ANSI_COLOR_NORMAL ANSI_ERASE_TO_EOL
            set BIGECHO_VALIDATED=1
        )


set PARAMS=%@UNQUOTE[%*]

setdos /x-678

    rem we use the ANSI_ERASE_TO_EOL sequence after setting the color to 'normal' to evade a Windows Terminal+TCC bug where the background color bleeds into the rightmost column
    %COLOR_TO_USE% %+  echo %BIG_TEXT_LINE_1%%PARAMS%%BIG_TEXT_END%%ANSI_COLOR_NORMAL%%ANSI_RESET%%ANSI_ERASE_TO_EOL%
    %COLOR_TO_USE% %+ echos %BIG_TEXT_LINE_2%%PARAMS%%BIG_TEXT_END%%ANSI_COLOR_NORMAL%%ANSI_RESET%%ANSI_ERASE_TO_EOL% %+ if %ECHOSBIG ne 1 (echo.)

    echos %BIG_TEXT_END%%ANSI_RESET%%ANSI_ERASE_TO_EOL%


setdos /x0

REM option should only affect it once
if defined COLOR_TO_USE (set COLOR_TO_USE=)

