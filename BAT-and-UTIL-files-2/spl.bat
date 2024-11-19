@Echo Off
@on break cancel
set DEBUG=0
set OUR_LOGGING_LEVEL=NONE

REM get post-split command
    set FULL_POST_SPLIT_COMMAND=%*
    set POST_SPLT_COMIMAND_ARGV0=%1

REM horizontal/vertical
    :Defaults
        set MODE=horizontal
        set COMMAND_TO_SPLIT_THE_SCREEN=%BAT%\split-windows-terminal-screen.ahk
    :CLI_overrides
        if "%1" eq "v" .or. "%1" eq "/v" .or. "%1" eq "-v" .or. "%1" eq "--v" .or. "%1" eq "--vertical"   .or. "%1" eq "vertical" (
            set FULL_POST_SPLIT_COMMAND=%2$
            set POST_SPLIT_COMMAND_ARGV0=%2
            set COMMAND_TO_SPLIT_THE_SCREEN=%BAT%\split-windows-terminal-screen-vertical.ahk
            set MODE=vertical
            shift
        )
        if "%1" eq "h" .or. "%1" eq "/h" .or. "%1" eq "-h" .or. "%1" eq "--h" .or. "%1" eq "--horizontal" .or. "%1" eq "horizontal" (
            set FULL_POST_SPLIT_COMMAND=%2$
            set POST_SPLIT_COMMAND_ARGV0=%2
            set COMMAND_TO_SPLIT_THE_SCREEN=%BAT%\split-windows-terminal-screen.ahk
            set MODE=horizontal
            shift
        )
        if "%POST_SPLIT_COMMAND_ARGV0" eq "/elevated" (
            call debug "Still developing this area of behavior..."
            pause

            call debug "POST_SPLIT_COMMAND_ARGV0[A]='%POST_SPLIT_COMMAND_ARGV0%', param1='%1', param2='%2'"
            set FULL_POST_SPLIT_COMMAND=%2$
            set POST_SPLIT_COMMAND_ARGV0=%2
            shift
            call debug "POST_SPLIT_COMMAND_ARGV0[B]='%POST_SPLIT_COMMAND_ARGV0%', param1='%1', param2='%2'"
    )
    
        REM Remind user of keypress because it's hard to remember when first using Windows Terminal:
            set KEY=Alt-Shift-D
            if "%mode%" eq "vertical" set KEY=Alt-Shift-=
            %COLOR_ADVICE% %+ echo - Split the screen %mode%ly with the %key% keypress


REM insert "call" before bat file commands, s that if EXIT_AFTER is turned in, we actualy return from the command to reach the 'exit' command in our generated POST_SPLIT_COMMAND_SCRIPT
    if "%1"                         eq "" goto :No_Parameters
    if "%POST_SPLIT_COMMAND_ARGV0%" eq "" goto :No_Parameters
        call detect-with-which %POST_SPLIT_COMMAND_ARGV0%
        set  DETECTED_SPLIT_COMMAND_ARGV0=%RESULT%
        set  DETECTED_SPLIT_COMMAND_ARGV0_EXTENSION=%@EXT[%DETECTED_SPLIT_COMMAND_ARGV0]
        if "%DETECTED_SPLIT_COMMAND_ARGV0_EXTENSION%" eq "bat" (
            call logging "it's a bat!"
            set FULL_POST_SPLIT_COMMAND=call %FULL_POST_SPLIT_COMMAND%
            set POST_SPLIT_COMMAND_ARGV0=call                                   
        ) else (
            call logging "it's not a bat!"
        )
    :No_Parameters

REM generate BAT file for post-split command:
    set POST_SPLIT_COMMAND_DIR=c:\TCMD\
    set POST_SPLIT_COMMAND_SCRIPT=%POST_SPLIT_COMMAND_DIR%\runonce-post-split.bat
                    
                                         echo @Echo OFF                  >:u8%POST_SPLIT_COMMAND_SCRIPT%
                                         echo %_CWD\                    >>:u8%POST_SPLIT_COMMAND_SCRIPT% %+ REM change into the same folder we issue this rom
    if "%FULL_POST_SPLIT_COMMAND%" ne "" echo %FULL_POST_SPLIT_COMMAND% >>:u8%POST_SPLIT_COMMAND_SCRIPT%
    if  %EXIT_AFTER_SPLIT_IS_RUN   eq  1 echo exit                      >>:u8%POST_SPLIT_COMMAND_SCRIPT%


    REM DEBUG: type "%POST_SPLIT_COMMAND_SCRIPT%" %+ pause
    call validate-environment-variables  POST_SPLIT_COMMAND_DIR POST_SPLIT_COMMAND_SCRIPT COMMAND_TO_SPLIT_THE_SCREEN



REM debugging
    call logging "mode: '%MODE%', FULL_POST_SPLIT_COMMAND is now '%FULL_POST_SPLIT_COMMAND%', POST_SPLIT_COMMAND_ARGV0='%POST_SPLIT_COMMAND_ARGV0%', DETECTED_SPLIT_COMMAND_ARGV0='%DETECTED_SPLIT_COMMAND_ARGV0%', DETECTED_SPLIT_COMMAND_ARGV0_EXTENSION='%DETECTED_SPLIT_COMMAND_ARGV0_EXTENSION%', ......................... contents of generated bat gfile:" 
    if %DEBUG gt 0 (%COLOR_DEBUG% %+ type %POST_SPLIT_COMMAND_SCRIPT%)
    call pause-if-debug




REM Actually split the screen:
    %COMMAND_TO_SPLIT_THE_SCREEN%

REM return focus back to calling window by hitting Alt-Left - TODO figure out when I would want to suppress this behavior? if i want to do something i'll just type it in the new window. if i want something to run, i'll put it in the command tail. so possibly i will never want to suppress this
    set KEY=
    set KEYSCRIPT=
    if "%mode%" eq "vertical" (
        set KEY=Alt-Up
        set KEYSCRIPT=%BAT%\send-keypress-alt_up.ahk
    ) else (
        set KEY=Alt-Left
        set KEYSCRIPT=%BAT%\send-keypress-alt_left.ahk
    )
    call validate-environment-variable KEY KEYSCRIPT
    %KEYSCRIPT%
