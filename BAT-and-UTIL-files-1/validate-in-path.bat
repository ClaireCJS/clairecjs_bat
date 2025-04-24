@loadbtm on
@echo %ansi_reset%%conceal_off%%ansi_color_grey%📞📞📞 “%0 %1$” called by %_PBATCHNAME 📞📞📞%ansi_color_normal%
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
   
   
rem Make sure stripansi plugin is loaded:   
        set stripansi_failed=0
        if "%@PLUGIN[stripansi]" == "" call load-TCC-plugins
        if "%@PLUGIN[stripansi]" == "" set stripansi_failed=1

rem Message styling experimentation:
        set PRIMARY_ERROR_MESSAGE_STYLING_ON=%italics_on%%blink_on%%@CHAR[27][48;2;128;24;24m
        set PRIMARY_ERROR_MESSAGE_STYLING_OFF=%blink_off%%italics_off%%ANSI_COLOR_FATAL_ERROR%


rem Custom error message:   
        iff "%validate_in_path_message%" != "" then
                set validate_in_path_message=%PRIMARY_ERROR_MESSAGE_STYLING_ON%%validate_in_path_message%%PRIMARY_ERROR_MESSAGE_STYLING_OFF%
        endiff




rem Now start validating!


   
set OUR_LOGGING_LEVEL=None
set PARAM2_WAS_A_MESSAGE=0

rem Process command line parameters:
        set CMDTAIL=
        set DO=1
        do while "%@UNQUOTE["%1"]" != ""
                set unquoted_command=%@UNQUOTE[%1]
                set already_validated_varname=validated_in_path_%1
                iff "1" == "%[%already_validated_varname%]" then
                        if defined debug .and. %DEBUG% gt 1 echo %star2% Command already validated as in our path: %italics_on%%already_validated_varname%%italics_off%
                elseiff "%@RegEx[You need,%unquoted_command%]" == "1" then
                        rem echo Message detected 🐈 %unquoted_command%
                        set  PARAM2_WAS_A_MESSAGE=1
                        iff  "%validate_in_path_message%" == ""  then
                                rem echo Initializing message 🐈 %unquoted_command%
                                set validate_in_path_message=%PRIMARY_ERROR_MESSAGE_STYLING_ON%%unquoted_command%%PRIMARY_ERROR_MESSAGE_STYLING_OFF%
                        else
                                rem echo Adding to existing message 🐈
                                iff "1" == "%stripansi_failed%" then
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


rem Validate each command line parameter
        rem echo 🐈 validate_in_path_message is %validate_in_path_message% 🐈
        rem echo 🐈 about to process CMDTAIL of %lq%%cmdtail%%rq%
        for %command in (%CMDTAIL%) do gosub validate_path_for_one_parameter %command%
        goto :cleanup

        :validate_path_for_one_parameter [command]
                rem Clean our command:
                        set clean_command=%command%
                        if "%@REGEXSUB[1,(.*)/(.*),%command]" != "" (set clean_command=%@REGEXSUB[1,(.*)/(.*),%command])

                rem Check if we’ve done it already:
                        set already_validated_varname=validated_in_path_%@UNQUOTE["%clean_command%"]
                        rem echo processing command %command% ... already_validated_varname = %lq%%already_validated_varname%%rq%

                rem Search for our [cleaned] command:
                        rem call logging "command=%command, clean_command=%clean_command"
                        set search_results=%@SEARCH[%clean_command]

                rem Is it a command or not?
                        set is_command=0
                        if isalias %clean_command% .or. isInternal %clean_command% .or. "%search_results%" != "" set is_command=1
                        rem echo %ansi_color_orange%validating command “%command%”  ... already_validated_varname == %lq%%already_validated_varname%%rq% ... clean_command=%lq%%clean_command%%rq% ... search_results=%lq%%search_results%%rq% ... is_command=%lq%%is_command%%rq%%ansi_color_normal%


                if "1" == "%is_command%" goto /i validation_passed
                                         goto /i validation_failed

                        :validation_failed
                                rem Debug:
                                        rem echo %ansi_color_orange%command doesn’t seem to exist%ansi_color_normal%
                                rem Create error message:
                                        set my_message=%PRIMARY_ERROR_MESSAGE_STYLING_ON%%clean_command%%PRIMARY_ERROR_MESSAGE_STYLING_OFF% is %italics_on%not%italics_off% in your path in %_PBATCHNAME, and needs to be %validate_in_path_message%
                                        rem echo unset /q validate_in_path_message
                                        unset /q validate_in_path_message
                                rem Display error message:
                                        call setpath 
                                        call fatal_error "%my_message%"
                                rem Attempt a quick in-place hotfix:
                                        call advice      "We will try setting the path again just in case"
                                        iff not isalias %clean_command% .and. not isInternal %clean_command% .and. "%search_results%" == "" then
                                                call warning "it didn’t seem to work?"
                                                pause
                                         else
                                                call success "it seemed to work?"
                                                pause
                                        endiff
                                goto /i validation_done

                        :validation_passed
                                rem Debug:
                                        rem echo %ansi_color_orange%command does seem to exist%ansi_color_normal%
                                rem Mark this one as already validated:
                                        set %already_validated_varname%=1                        

                        :validation_done
        return

rem Once more for good measure:
        :END
        :cleanup
        unset /q validate_in_path_message
        if defined CURSOR_RESET echos %CURSOR_RESET%
        rem @echo %ansi_reset%%conceal_off%%ansi_color_grey%📞📞📞 ENDING: “%0 %1$” called by %_PBATCHNAME 📞📞📞%ansi_color_normal%
     


