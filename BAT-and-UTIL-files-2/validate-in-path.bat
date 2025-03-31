@echo %ansi_reset%%conceal_off%%ansi_color_grey%📞📞📞 “%0 %1$” called by %_PBATCHNAME 📞📞📞%ansi_color_normal%
@echo off
@loadbtm on
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
   
   
rem Make sure stripansi plugin is loaded:   
        set stripansi_failed=0
        if "%@PLUGIN[stripansi]" eq "" call load-TCC-plugins
        if "%@PLUGIN[stripansi]" eq "" set stripansi_failed=1

rem Message styling experimentation:
        set PRIMARY_ERROR_MESSAGE_STYLING_ON=%italics_on%%blink_on%%@CHAR[27][48;2;128;24;24m
        set PRIMARY_ERROR_MESSAGE_STYLING_OFF=%blink_off%%italics_off%%ANSI_COLOR_FATAL_ERROR%


rem Custom error message:   
        iff "%validate_in_path_message%" ne "" then
                set validate_in_path_message=%PRIMARY_ERROR_MESSAGE_STYLING_ON%%validate_in_path_message%%PRIMARY_ERROR_MESSAGE_STYLING_OFF%
        endiff




rem Now start validating!


   
set OUR_LOGGING_LEVEL=None
set PARAM2_WAS_A_MESSAGE=0
set CMDTAIL=
set DO=1
do while "%1" ne ""
        set unquoted_command=%@UNQUOTE[%1]
        iff "%@RegEx[You need,%unquoted_command%]" eq "1" then
                rem echo Message detected 🐈 %unquoted_command%
                set  PARAM2_WAS_A_MESSAGE=1
                iff  "%validate_in_path_message%" eq ""  then
                        rem echo Initializing message 🐈 %unquoted_command%
                        set validate_in_path_message=%PRIMARY_ERROR_MESSAGE_STYLING_ON%%unquoted_command%%PRIMARY_ERROR_MESSAGE_STYLING_OFF%
                else
                        rem echo Adding to existing message 🐈
                        iff 1 eq %stripansi_failed% then
                                rem echo      ...Using stripansi 🐈
                                set validate_in_path_message=%@STRIPANSI[%validate_in_path_message%]
                        else
                                rem echo      ...NOT Using stripansi 🐈                        
                        endiff
                        set validate_in_path_message=%italics_on%%validate_in_path_message%%italics_off% ... %PRIMARY_ERROR_MESSAGE_STYLING_ON%%unquoted_command%%PRIMARY_ERROR_MESSAGE_STYLING_OFF%
                endiff
        else
                set CMDTAIL=%CMDTAIL% %1
                rem echo Message not detected 🐈 ... tail is now %CMDTAIL%
        endiff
        shift
enddo

rem echo 🐈 validate_in_path_message is %validate_in_path_message% 🐈

for %command in (%CMDTAIL%) do (
        set clean_command=%command%
        if "%@REGEXSUB[1,(.*)/(.*),%command]" ne "" (set clean_command=%@REGEXSUB[1,(.*)/(.*),%command])
        rem call logging "command=%command, clean_command=%clean_command"
        set search_results=%@SEARCH[%clean_command]
        iff not isalias %clean_command .and. not isInternal %clean_command .and. "%search_results%" eq "" then
                set my_message=%PRIMARY_ERROR_MESSAGE_STYLING_ON%%clean_command%%PRIMARY_ERROR_MESSAGE_STYLING_OFF% is %italics_on%not%italics_off% in your path, and needs to be. %validate_in_path_message%
                rem echo unset /q validate_in_path_message
                unset /q validate_in_path_message
                call fatal_error "%my_message%"
                call advice      "We will try setting the path again just in case"
                call setpath 
                iff not isalias %clean_command .and. not isInternal %clean_command .and. "%search_results%" eq "" then
                        %COLOR_WARNING% 
                        echo it didn’t seem to work?
                 else
                        %COLOR_SUCCESS%
                        echo it seemed to work?
                endiff
        endiff
)

rem Once more for good measure:
        unset /q validate_in_path_message
        echos %CURSOR_RESET%
        