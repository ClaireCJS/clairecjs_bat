@echo off
@on break cancel

:PUBLISH:
:DESCRIPTION: validates if commands are valid
:USAGE:   set validate_in_path_message={optional additional error message}
:USAGE:       validate-in-path {list of commands to validate}
:EXAMPLE:     validate-in-path grep awk whatever.exe whatever.bat dir cmd.exe anything_really.py


rem    Complication #1: What if we are passed an alias?   
rem                     [Solution: add isalias check]

rem    Complication #2: Windows command lines let us do commands like "dir/s" without space before the slash, 
rem                     [Solution: use regular epressions to strip things off past a slash into a clean command]
   
set OUR_LOGGING_LEVEL=None

for %command in (%*) do (
    set clean_command=%command%
    if "%@REGEXSUB[1,(.*)/(.*),%command]" ne "" (set clean_command=%@REGEXSUB[1,(.*)/(.*),%command])
    rem call logging "command=%command, clean_command=%clean_command"
    set search_results=%@SEARCH[%clean_command]
    if not isalias %clean_command .and. not isInternal %clean_command .and. "%search_results%" eq "" (
        set my_message=FATAL ERROR! %clean_command is not in your path, and needs to be. %validate_in_path_message%
        unset /q validate_in_path_message
        call fatal_error "%my_message%"
        call advice      "We will try setting the path again just in case"
        call setpath 
        if not isalias %clean_command .and. not isInternal %clean_command .and. "%search_results%" eq "" (
            %COLOR_WARNING% 
            echo it didn't seem to work?
        ) else (
            %COLOR_SUCCESS%
            echo it seemed to work?
        )
    )
)
