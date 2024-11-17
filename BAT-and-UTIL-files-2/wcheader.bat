@echo off

:DESCRIPTION: This is a cosmetic assistant to wc (unix wordcount util) that prints a header over the numbers, so that we know what they are
:DESCRIPTION: It takes the same command-line option as wc
:DESCRIPTION: NOTE: The headers don't actually line up perfectly —— that would require postprocessing wc itself to line up the columns
:DESCRIPTION: It does not actually run wc. For that, use wcnice.bat/wcpretty.bat

if "%1"=="-w"  goto :w
if "%1"=="-l"  goto :l
if "%1"=="-c"  goto :c
if "%1"=="-lc" goto :lc
if "%1"=="-cl" goto :lc
if "%1"=="-wl" goto :wl
if "%1"=="-lw" goto :wl
if "%1"=="-cw" goto :cw
if "%1"=="-wc" goto :cw

rem We don't need to worry about all the permutations of the 3 letters in "-wcl" - they all fall under the default scenario

goto :default

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:cw
    echo   WORDS    SIZE   FILE
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:wl
    echo   WORDS   LINES   FILE
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:w
    echo   WORDS   FILE
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:c
    echo    SIZE   FILE
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:l
    echo   LINES   FILE
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:lc
    echo   LINES  SIZE  FILE
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:default
    echo   LINES  WORDS  SIZE  FILE
goto :end
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:end

