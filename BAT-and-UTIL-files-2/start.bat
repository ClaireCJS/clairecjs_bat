@Echo On
 on break cancel
REM set logging=None
REM call logging "%0 %*"

REM Capture parameters
        set COMMAND_TAIL=%*


REM 2023: protect us from improper invocation changes due to window 10 changes
        if "%1" eq "" (
            call advice "Start is now aliased to a bat file because of invocation differences that started with windows 10"
            *start /? 
            goto :END
        )


REM This is the command that we would be using, after Windows 10 but prior to beginning to use Windows Terminal:
        set START_COMMAND=*start `""` %COMMAND_TAIL
        rem if %DEBUG gt 0 
        echo %ANSI_COLOR_DEBUG%start_command is '%START_COMMAND%'%ANSI_COLOR_NORMAL%

REM 2023 Windows Terminal introduced window panes, and we start using these for more "start" cases
        call detect-command-line-container
        if %MAKE_STARTBAT_USE_STARTEXE eq 1 .or. %TRADITIONAL_START eq 1 (set use_start=1)

        REM if there are parameters, we probably have *start-specific behavior and probably shouldn't split to a new pane:
        if "%1" eq "/inv" set use_start=1

        REM if it's an EXE, it probably won't have a lot of console output, so probably shouldn't split to a new pane:
        REM (if something just opens a bunch of windows splits instead of what it should do, try adding its extension here)
        if "%@UPPER[%@EXT[%1]]" eq "EXE" set use_start=1
        if "%@UPPER[%@EXT[%1]]" eq "ZIP" set use_start=1
        if "%@UPPER[%@EXT[%1]]" eq "MSI" set use_start=1
        if "%@UPPER[%@EXT[%1]]" eq "7Z"  set use_start=1
        REM TODO it may be that if it's not a bat/btm then we should not split!


        call print-if-debug "start_command is '%START_COMMAND%', %blink%use_start='%use_start%'%blink_off%" %+ call pause-if-debug
        if "%container" eq "WindowsTerminal" .and. %use_start ne 1 (
            if "%LAST_SPLIT" eq "vertical" (
                set SPLITTER=splh
                set LAST_SPLIT=horizontal
            ) else (
                set SPLITTER=splv
                set LAST_SPLIT=vertical
            )
            set START_COMMAND=call %SPLITTER% %COMMAND_TAIL
        ) else (
            if defined MAKE_STARTBAT_USE_STARTEXE (unset /q MAKE_STARTBAT_USE_STARTEXE)
            if defined TRADITIONAL_START          (unset /q TRADITIONAL_START         )
        )
        call print-if-debug "start_command is '%START_COMMAND%'" %+ call pause-if-debug
        call print-if-debug "        [container is '%CONTAINER%'] [last_split is '%LAST_SPLIT%'] [command tail='%COMMAND_TAIL']" %+  call pause-if-debug

REM Actually do our command:
        %START_COMMAND%

:END