@echo off

rem Used to submit following bug report to Microsoft Terminal: https://github.com/microsoft/terminal/issues/17771

rem note that "%@CHAR[27]" creates the ESC character
rem note that "repeat 2 echo." is how we make 2 blank lines
rem note that ANSI_RESET is a set of codes to reset all ANSI colors and formatting
rem note that BIG_TOP and BIG_BOT are the ANSI codes for double-height lines (top and bottom lines)


repeat 2 echo.

            
rem Define ANSI sequences:
        set ANSI_ESCAPE=%@CHAR[27][
        set ANSI_RESET=%ANSI_ESCAPE%39m%ANSI_ESCAPE%49m%ANSI_ESCAPE%0m

        set ANSI_FOREGROUND_BRIGHT_WHITE=%ANSI_ESCAPE%97m
        set ANSI_BACKGROUND_RED=%ANSI_ESCAPE%41m
        set ANSI_BRIGHT_WHITE_ON_RED=%ANSI_FOREGROUND_BRIGHT_WHITE%%ANSI_BACKGROUND_RED%

        set ANSI_ERASE_TO_END_OF_LINE=%ANSI_ESCAPE%0K                   
        set BIG_TOP=%ESCAPE%#3
        set BIG_BOT=%ESCAPE%#4
        set BIG_OFF=%ESCAPE%#0

echo ——— Verify our ansi codes: 
echo %ANSI_BRIGHT_WHITE_ON_RED% bright white on red %ANSI_RESET%  normal  %ansi_background_red% red background %ANSI_RESET%  normal %ANSI_FOREGROUND_BRIGHT_WHITE% bright white %ANSI_RESET% normal 
repeat 2 echo.

echo ——— Cosmetically correct (ends with big-off+ansi-reset on both lines, erase to EOL on bottom line): 
echo %BIG_TOP% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE %BIG_OFF%%ANSI_RESET%
echo %BIG_BOT% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE %BIG_OFF%%ANSI_RESET%%ANSI_ERASE_TO_END_OF_LINE%
echo.

echo ——— Cosmetically correct (ends with big-off+ansi-reset on both lines, NO erasing to EOL on bottom line): 
echo %BIG_TOP% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE %BIG_OFF%%ANSI_RESET%
echo %BIG_BOT% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE %BIG_OFF%%ANSI_RESET%
echo.

echo ——— Cosmetically incorrect (ends with only big_off on both lines, but no ansi-rest or erasing to EOL on either line)
echo ——— I do not think this 
echo %BIG_TOP% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE %BIG_OFF%
echo %BIG_BOT% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE %BIG_OFF%
echo %ANSI_RESET%[Ansi is reset here yet red bleeds to the right still even though the background color was reset to black/49m]
echo.

echo ——— Cosmetically incorrect (nothing at the end of the line, which is how I think most would do this)
echo ——— I do not think this 
echo %BIG_TOP% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE
echo %BIG_BOT% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE
echo %ANSI_RESET%[Ansi is reset here yet red bleeds through and we find ourselves one line lower than expected--SURPRISE BLANK LINE?!?!]
echo.

echo ——— Cosmetically correct (ends with ansi-reset on both lines, NO big-off or erasing to either line): 
echo %BIG_TOP% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE %ANSI_RESET%
echo %BIG_BOT% %ANSI_BRIGHT_WHITE_ON_RED% TEST MESSAGE %ANSI_RESET%
echo.


