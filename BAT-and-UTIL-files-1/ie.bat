@on break cancel
@echo off

REM NO :PUBLISH:
:DESCRIPTION: This is a simple bat to let you run ie at the command line.
:USAGE: 'ie' simply goes to whatever URL is in the clipboard, if any.
:USAGE: 'ie http://www.yahoo.com' would go to yahoo
:SEE: 'iehere' bat runs ie (explorer) in the current folder
:REQUIRES: 4DOS (for %@CLIP clipboard manipulation)

::::: CONSTANTS:
    set LAST_BROWSER=start iexplore.exe

::::: CAPTURE URL:
                           set URL=%1
    if "%URL" eq ""        set URL=%@CLIP[0]
    if "%URL" eq "**EOC**" set URL=
    %COLOR_DEBUG%   %+    echo URL is %URL .. %1 %2 %3

::::: OTHER OPTIONS:
    if "%MACHINENAME" eq "HADES" set START=0
    if "%MACHINENAME" eq "HADES" goto :URLOnly
    if "%START"       eq "0"     goto :nostart

::::: DEFAULT BEHAVIOR:
    goto :start

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :start
         set REDOCOMMAND=%LAST_BROWSER %URL
        %COLOR_DEBUG% %+ echo * IE.BAT start command is: %REDOCOMMAND%
        %COLOR_RUN%   %+                                 %REDOCOMMAND%
    goto :CLEANUP

    :nostart
         %LAST_BROWSER% %URL%
    goto :CLEANUP

    :URLOnly
        echo URL is %URL%
                    %URL%
    goto :CLEANUP
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



:CLEANUP
    set LAST_URL_OPENED_BY_IE_BAT=%URL%
    UNSET /q URL
    %COLOR_NORMAL% 
