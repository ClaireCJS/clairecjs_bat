@loadbtm on
@echo off
@on break cancel
@rem echo %ansi_reset%%conceal_off%%ansi_color_grey%📞📞📞 “%0 %1$” called by %_PBATCHNAME 📞📞📞%ansi_color_normal%
gosub save_cusor_position
gosub display_temp_output

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
rem If it’s still not loaded even after trying, take special note of it:
        if "%@PLUGIN[stripansi]" == "" set stripansi_failed=1


rem Make sure ansi_move_to function is defined:
        if "" == "%@FUNCTION[ansi_move_to]" function ANSI_MOVE_TO=`%@CHAR[27][%1H%@CHAR[27][%2G`        
        if "" == "%@function[RANDFG_SOFT]"  goto :endif_66
                        rem echo redefining randfg_soft.... %+ pause
                rem (copied from set-ansi.bat):
                        set MIN_RGB_VALUE_FG=88
                        set MAX_RGB_VALUE_FG=255
                        set MIN_RGB_VALUE_BG=12
                        set MAX_RGB_VALUE_BG=40
                        set EMPHASIS_BG_EXPANSION_FACTOR=1.4
                        set MIN_RGB_VALUE_BG=%@FLOOR[%@EVAL[%MIN_RGB_VALUE_BG*%EMPHASIS_BG_EXPANSION_FACTOR%]]
                        Set MAX_RGB_VALUE_BG=%@FLOOR[%@EVAL[%MAX_RGB_VALUE_BG*%EMPHASIS_BG_EXPANSION_FACTOR%]]
                        function RANDFG_SOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m`
        :endif_66
        rem if "" == "%@FUNCTION[ansi_move_to]" call set-ansi force


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
        set any_path_validations_failed=0
        for %command in (%CMDTAIL%) do (gosub restore_cusor_position %+ gosub display_temp_output %+ gosub validate_path_for_one_parameter %command%)
        goto :cleanup


:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

                                rem Track that there were any failures at all:
                                        set any_path_validations_failed=1
                                rem Create error message:
                                        set my_message=%PRIMARY_ERROR_MESSAGE_STYLING_ON%%clean_command%%PRIMARY_ERROR_MESSAGE_STYLING_OFF% is %italics_on%not%italics_off% in your path in %_PBATCHNAME, and needs to be %validate_in_path_message%
                                        rem echo unset /q validate_in_path_message
                                        unset /q validate_in_path_message
                                rem Display error message:
                                        call setpath 
                                        gosub restore_cusor_position
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
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :save_cusor_position []
                set vip_saved_row=%_row
                set vip_saved_col=%_col
        return
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :restore_cusor_position []
                echos %@ansi_move_to[%@EVAL[%vip_saved_row% + 1],%@EVAL[%vip_saved_col% + 1]]
        return
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :display_temp_output []
                set coloring=`%@randfg_soft[]`
                echos %ansi_cursor_invisible%%coloring%P%coloring%%faint_on%?%faint_off%%ansi_color_reset%
                set temp_output_vip_length=2
        return
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


rem Ending stuff / cleanup:
        :END
        :cleanup
                unset /q validate_in_path_message
                rem if defined ANSI_CURSOR_VISIBLE echos %ANSI_CURSOR_VISIBLE%
                if defined CURSOR_RESET        echos %CURSOR_RESET%
     
rem Erase temp output:
        iff "1" != "%any_path_validations_failed%" then
                gosub restore_cusor_position
                echos %@REPEAT[ ,%temp_output_vip_length%]``
                gosub restore_cusor_position
        endiff

rem DEBUG:
        rem @echo %ansi_reset%%conceal_off%%ansi_color_grey%📞📞📞 ENDING: “validate-in-path $*” called by %_PBATCHNAME 📞📞📞%ansi_color_normal%
