@echo off

::::: SETUP:
    if not defined USERNAME (echo *** FATAL ERROR: USERNAME NOT DEFINED! %+ pause +% goto :END)
    call validate-environment-variable COLOR_ALARM
    call validate-environment-variable COLOR_NORMAL

::::: FLASH WINDOW AND DISPLAY ERROR:
    window flash=2,8
    :window flash=4
    if "%1" eq "" goto :NoErrorToDisplay
        %COLOR_ALARM%   %+    echos *** ERROR: %* ***     %+        %COLOR_NORMAL%
    :NoErrorToDisplay

::::: DON'T MAKE AUDIBLE ALARM IF SOMEONE IS NAPPING:
    if "%SLEEPING%" eq "1" goto :done_klaxoning
        gosub klaxon
        gosub klaxon
        gosub klaxon
        gosub klaxon
    :done_klaxoning





goto :END

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:klaxon
goto :klaxon%USERNAME%

    :klaxon
    :klaxonClaire
        beep  2000 10
        beep  1000 10
        call sleep 1 silent
    return

    :klaxonCarolyn
        beep  2666 2
        beep  1333 2
        beep  2666 2
        call sleep 1 silent
    return

    :klaxonCarolynRejected
        beep  1333 2
        beep  2666 1
        beep  1333 1
        beep  2666 1
        beep  1333 1
        call sleep 1 silent
    return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
    :stop continuous flashing:
    :window flash=0
    :start non-continuous flashing that, in theory, goes until the window is in the foreground again, but, in reality, doesn't always if new commands are issued in a BAT file:
    window flash=2,8
    window flash=2,2
    pause

