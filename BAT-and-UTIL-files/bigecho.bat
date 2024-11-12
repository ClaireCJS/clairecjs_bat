@echo off
@on break cancel


:DESCRIPTION: Uses DEC VT100 ANSI codes to echo a line in double-height text

:DEPRECATED: optionally set COLOR_TO_USE=<command to set the color to use> prior to calling for cosmetically better background color handling to avoid the cosmetic weirdness of newlines with a different background color (likely no longer necessary after 20241015 changes)


rem Get parameters:
        set PARAMS=%@UNQUOTE[%*]


rem Validate environment
        if %BIGECHO_VALIDATED ne 1 (
            if not defined BIG_TEXT_LINE_1 (call error "BIG_TEXT_LINE_1 is not defined. Try running set-colors.bat")
            if not defined BIG_TEXT_LINE_2 (call error "BIG_TEXT_LINE_2 is not defined. Try running set-colors.bat")
            call validate-environment-variables BIG_TEXT_LINE_1 BIG_TEXT_LINE_2 BIG_TEXT_END ANSI_RESET ANSI_COLOR_NORMAL ANSI_ERASE_TO_EOL emphasis deemphasis blink_on blink_off
            set BIGECHO_VALIDATED=1
        )

rem If it's too wide  then simply revert back to echo'ing the command in normal/single-height lines...
        set LEN=%@LEN[%@stripansi[%PARAMS]]

rem This false positives to not-double-height on unicode/characters that are hard to measure the width of accurately and which report lenghts greater than printable length...
        set FUDGE_FACTOR=7
        if not %@EVAL[%len*2] lt %@EVAL[%_COLUMNS-%FUDGE_FACTOR%]    (echo %STAR%%STAR%%STAR% %blink_on%%emphasis%%1$%deemphasis%%blink_off% %STAR%%STAR%%STAR% %+ goto :END)

setdos /x-678

    rem We will move to column 1, because switching to big text mid-column makes no sense!
    echos %@ANSI_MOVE_TO_COL[1]

    rem we use the ANSI_ERASE_TO_EOL sequence after setting the color to 'normal' to evade a Windows Terminal+TCC bug where the background color bleeds into the rightmost column
    rem %COLOR_TO_USE% %+  echo %BIG_TEXT_LINE_1%%PARAMS%%BIG_TEXT_END%%ANSI_COLOR_NORMAL%%ANSI_RESET%%ANSI_ERASE_TO_EOL%
    rem %COLOR_TO_USE% %+ echos %BIG_TEXT_LINE_2%%PARAMS%%BIG_TEXT_END%%ANSI_COLOR_NORMAL%%ANSI_RESET%%ANSI_ERASE_TO_EOL% %+ if %ECHOSBIG ne 1 (echo.)
    rem echos %BIG_TEXT_END%%ANSI_RESET%%ANSI_ERASE_TO_EOL%

    rem There was a lot of weirdness with background color bleedthrough:
    rem I opened this bug report with Windows Terminal to fix it: 
    rem https://github.com/microsoft/terminal/issues/17771
    rem But it turned out to not be a bug, and this is just what we have to do:

    if %ECHOSBIG_NEWLINE_AFTER eq 1 (set XX=2 %+ echos %@ANSI_MOVE_DOWN[%xx]%@ANSI_MOVE_UP[%@EVAL[%xx-1]]%@ANSI_MOVE_TO_COL[1])



    rem OR_TO_USE% %+ echos %BIG_TEXT_LINE_1%%PARAMS% %+ echos %BIG_TEXT_END%%ANSI_RESET%           %+ if %ECHOSBIG_SAVE_POS_AT_END_OF_TOP_LINE eq 1 (echos %ANSI_SAVE_POSITION%)  

    %COLOR_TO_USE% 

    rem echos %BIG_TEXT_LINE_1%%PARAMS%%ANSI_EOL%             
    rem deprecated if %ECHOSBIG_SAVE_POS_AT_END_OF_TOP_LINE eq 1 (echos %ANSI_SAVE_POSITION%)  
    REM echo.
    rem OR_TO_USE% %+ echos %BIG_TEXT_LINE_2%%PARAMS% %+ echos %BIG_TEXT_END%%ANSI_RESET%%ANSI_EOL% %+ if %ECHOSBIG_SAVE_POS_AT_END_OF_BOT_LINE eq 1 (echos %ANSI_SAVE_POSITION%)  
    rem %COLOR_TO_USE% 

    echos %BIG_TEXT_LINE_1%%PARAMS%%ANSI_EOL%%NEWLINE%%BIG_TEXT_LINE_2%%PARAMS%%BIG_TEXT_END%%ANSI_EOL%
   
    rem deprecated: if %ECHOSBIG_SAVE_POS_AT_END_OF_BOT_LINE eq 1 (echos %ANSI_SAVE_POSITION%)  
    rem echo.

    echos %ANSI_RESET%
    if %ECHOSBIG ne 1 (echo.)

    echos %@ANSI_MOVE_UP[1]
    echo.
    if %ECHOSBIG_NEWLINE_AFTER eq 1 (echo. %+ echo.)


:END
    setdos /x0
    REM This option should only affect it once, and thus needs to self-delete:
            if defined COLOR_TO_USE (set COLOR_TO_USE=)

