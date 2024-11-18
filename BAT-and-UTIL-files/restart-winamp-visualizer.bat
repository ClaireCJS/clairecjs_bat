@echo on

rem Validate environment:
        call validate-in-path restart-taskbar-autohide LaunchKey sleep

rem Make sure taskbar autohide is running, so that Win-A keystroke works:
        call restart-taskbar-autohide

rem Hit Win-A to turn off taskbar: (requires AutoHotKey Basic to be installed):
        LaunchKey "#a"
        call sleep 2
        rem ^20120301 changed from 1 to 2 cause it keeps failing as if things are ever-so-slightly lagged


rem Send ctrl-shift-K to winamp, to start visualizer:
        LaunchKey "+^K" "%ProgramFiles\Winamp\winamp.exe"
        call sleep 4

rem Send Alt-D to winamp, which has 3 sub-windows that we must control-tab between 
rem  so that Alt-D hits each of the 3 sub-windows, ensuring it hits the right one
rem  we'll do it a couple extra times because sometimes it doesn't seem to catch
        LaunchKey.exe "^{TAB}%%D^{TAB}%%D^{TAB}%%D^{TAB}%%D^{TAB}%%D" "%ProgramFiles\Winamp\winamp.exe"
        call sleep 3

rem Hit Win-A to turn back on taskbar: (requires AutoHotKey Basic to be installed):
        LaunchKey "#a"
        call sleep 1

