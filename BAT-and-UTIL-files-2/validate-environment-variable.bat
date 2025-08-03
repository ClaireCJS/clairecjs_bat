@loadbtm on
@rem @echo %ansi_reset%%conceal_off%%ansi_color_orange%📞📞📞 “%0 %1$” called by %_PBATCHNAME / %PBATCH2% 📞📞📞%ansi_color_normal%
@Echo off
@on break cancel
@setdos /x0
if defined italics_on set italics_maybe=%italics_on%
gosub save_cusor_position
rem pause "about to gosub display_temp_output"
gosub display_temp_output
rem why won’t this work for this bat? @setlocal

::::: GET PARAMETERS:
    set LAST_TITLE=%_TITLE
    set VEVPARAMS=%1$
    set VARNAME=%1      
    set PARAM2=%2
    set PARAM3=%3
    set USER_MESSAGE=%2$
    if %DEBUG_VALIDATE_ENV_VAR% eq 1 (echo %DEBUGPREFIX% if defined %VARNAME% goto :Defined_YES)
    set LAST_TITLE=%_WINTITLE
    title %0

:USAGE:  call validate-environment-variable VARNAME_NO_PERCENT [a custom error message] or "skip_validation_existence"
:USAGE:       where option can be:
:USAGE:                             "skip_validation_existence" to skip existence validation
:USAGE:                             "some error message"        to be additional information provided to user if there is an error

:REQUIRES: exit-maybe.bat, warning.bat, fatalerror.bat, white-noise.bat (optional), bigecho.bat (optional)
:                                       REM car.bat, nocar.bat removed from requires 20230825


::::: DEBUG STUFFS:
    rem echo %ANSI_COLOR_DEBUG% %0 called with 1=%1, 2=%2, VARNAME=%VARNAME%, VEVPARAMS=%VEVPARAMS% %ANSI_COLOR_RESET%


::::: CLEAR LONGTERM ERROR FLAGS:
    set DEBUG_VALIDATE_ENV_VAR=0
    set DEBUG_NORMALIZE_MESSAGE=0
    set ERROR_MESSAGE=
    set ERROR=0
    set any_env_var_validations_failed=0

::::: CLEAR LONGTERM ERROR FLAGS:
    set ENVIRONMENT_VALIDATION_FAILED=0
    set ENVIRONMENT_VALIDATION_FAILED_NAME=
    set ENVIRONMENT_VALIDATION_FAILED_VALUE=
    set DEBUGPREFIX=- {validate-environment-variable} * ``
    
::::: GET CALLING-BAT-FILE INFO, INCLUDING THAT MANUALLY PASSED FROM GRANDPARENT BATCH FILE:
        set OUR_CALLER=%_PBATCHNAME
        if "%_PBATCHNAME" == "%bat%\validate-environment-variables.bat" .and. defined PBATCH2 .and. "" != "%PBATCH2%" (set OUR_CALLER=%PBATCH2%)
        set OUR_CALLER=%@NAME[%our_caller].%@EXT[%our_caller]
    
::::: VALIDATE ENVIRONMENT:
rem Make sure ansi_move_to function is defined:
        if "" == "%@function[ANSI_MOVE_TO]" function ANSI_MOVE_TO=`%@CHAR[27][%1H%@CHAR[27][%2G`        
        if "" != "%@function[RANDFG_SOFT]"  goto :endif_66
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
        iff "1" !=  "%validated_validate_env_vars%" .and. not defined FILEMASK_ALL_REGEX then
                gosub restore_cusor_position
                %color_warning%
                echo WARNING in validate-environment-variable.bat when called by %OUR_CALLER%: FILEMASK_ALL_REGEX not defined!
                if defined PBATCH2 echo       grandparent BAT = %PBATCH2%
                pause
                goto :END
        else
                set validated_validate_env_vars=1
        endiff



::::: VALIDATE PARAMETERS STRICTLY
    rem call debug "param3            is %param3%"
    rem call debug "validate_multiple is %validate_multiple%"
    rem call debug "about to check if PARAM3 [%param3%] ne '' .and. VALIDATE_MULTIPLE [%VALIDATE_MULTIPLE] ne 1 .... ALL_PARAMS is: %VEVPARAMS%"
    if "%@NAME[%OUR_CALLER%]" == "validate-environment-variables" set VALIDATE_MULTIPLE=1
    iff "%PARAM3%" != "" .and. "%VALIDATE_MULTIPLE%" != "1" then
        gosub restore_cusor_position
        call bigecho "%ANSI_COLOR_ALARM%%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] ENV VAR ERROR! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]"
        color bright white on red
        echo  We can’t be passing a %italics%%blink%third%blink_off%%italics_off% parameter to validate-environment-variable.bat 
        echo  %underline%Did you mean%underline_off%: %italics%validate-environment-variable%double_underline%%blink%s%blink_off%%double_underline_off% %VEVPARAMS%%italics_off% 
        echo                                   (with an %left_quote%s%right_quote% after %left_quote%%italics%variable%italics_off%%right_quote%)  ????

        call exit-maybe
        if %FORCE_EXIT eq 1 (goto :END)
        
        set VEV_COMMENT=repeat 4 beep
        set VEV_COMMENT=repeat 25 *pause

        goto :END
    endiff

    set SKIP_VALIDATION_EXISTENCE=0
    if "%PARAM2%" == "skip_validation_existence" .or. "%PARAM2%" == "skip_existence_validation" .or. "%PARAM2%" == "skip_validation" (
        set SKIP_VALIDATION_EXISTENCE=1 
        set USER_MESSAGE=%3$
    )
    if %DEBUG_NORMALIZE_MESSAGE eq 1 (gosub restore_cusor_position %+ echo %ansi_color_debug%- DEBUG: PARAM2: %left_quotes%%PARAM2%%right_quotes%%ansi_color_normal%)


    iff "1" != "%VALIDATE_MULTIPLE%" then
        gosub validate_environment_variable %VARNAME%

        rem If this script gets aborted, leaving this flag set can create false errors:
                unset /q VALIDATE_MULTIPLE 
    else 
        set USER_MESSAGE=
        do i = 1 to %# 
                gosub restore_cusor_position
                gosub display_temp_output            %[%i]
                gosub validate_environment_variable  %[%i]
        enddo
    endiff





:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
goto :Past_The_End_Of_The_Subroutines


    :validate_environment_variable [VARNAME]
        rem debug: echo validate_environment_variable %varname%
        rem echos %@RANDCURSOR[]
        ::::: SEE IF IT IS DEFINED:
            if defined %VARNAME% (goto :Defined_YES)
            if ""  ==  %VARNAME% (goto :Defined_NO )

                    ::::: RESPOND IF IT IS NOT DEFINED/EXISTING:
                        :Defined_NO
                            gosub restore_cusor_position
                            set any_env_var_validations_failed=1
                            set ERROR=1
                            set ERROR_MESSAGE=%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] Environment variable %left_quote%%underline%%italics%%blink%%varname%%italics_off%%blink_off%%underline_off%%right_quote% is %double_Underline%not%double_Underline_off% defined, and needs to be
                            if "" !=  "%OUR_CALLER%" set ERROR_MESSAGE=%ERROR_MESSAGE%, in %italics_on%%left_quotes%%@name[%our_caller%].%@ext[%our_caller%]%right_quote%%italics_off%
                            set ERROR_MESSAGE=%ERROR_MESSAGE%!!! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]
                            if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo - DEBUG: ERROR_MESSAGE[1]: %ERROR_MESSAGE% [length_diff=%LENGTH_DIFF%] [errlen=%ERROR_LENGTH,userlen=%USER_LENGTH])
                            if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo - DEBUG: `%`USER_MESSAGE`%` is %left_quotes%%USER_MESSAGE%%right_quotes%)
                            if "%USER_MESSAGE%" != "" goto :Do_It_1
                                                      goto :Do_It_1_Done
                            :Do_It_1
                                REM Normalize width of ERROR_MESSAGE to be same width as USER_MESSAGE
                                if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo - DEBUG: User message found)

                                rem Get the length of both variables
                                set "ERROR_LENGTH=%@LEN[%ERROR_MESSAGE]"
                                set  "USER_LENGTH=%@LEN[%USER_MESSAGE%]"

                                rem Calculate the difference in length
                                set /a "LENGTH_DIFF=!USER_LENGTH! - !ERROR_LENGTH!"

                                REM for /L %%i in (1,1,%LENGTH_DIFF%) do (set EXCLAMATION_MARKS=%EXCLAMATION_MARKS%!)
                                REM 
                                REM rem Substitute the final sequence of exclamation marks in ERROR_MESSAGE
                                REM if DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo - DEBUG: EXCLAMATION_MARKS is %left_quotes%%EXCLAMATION_MARKS%%right_quotes%)
                                REM set NORMALIZED_ERROR_MESSAGE=%@REPLACE[!!!,%EXCLAMATION_MARKS%,%ERROR_MESSAGE%]
                                REM set ERROR_MESSAGE=%NORMALIZED_ERROR_MESSAGE%

                                iff %LENGTH_DIFF% lss 0 then
                                    set /a "LENGTH_DIFF=-%LENGTH_DIFF% / 2"
                                endiff
                                iff %LENGTH_DIFF% lss 0 then
                                    rem If USER_MESSAGE is longer
                                    for /L %%i in (1,1,%LENGTH_DIFF%)    do   (set "ERROR_MESSAGE=*%ERROR_MESSAGE%*")
                                    if          %@EVAL[%LENGTH_DIFF % 2] == 0 (set "ERROR_MESSAGE=%ERROR_MESSAGE%*" )
                                else
                                    rem If ERROR_MESSAGE is longer
                                    for /L %%i in (1,1,%LENGTH_DIFF%)    do   (set "USER_MESSAGE=*%USER_MESSAGE%*")
                                    if          %@EVAL[%LENGTH_DIFF % 2] == 0 (set "USER_MESSAGE=%USER_MESSAGE%*" )
                                endiff

                            :Do_It_1_Done
                            if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo ERROR_MESSAGE[2]: %ERROR_MESSAGE% [length_diff=%LENGTH_DIFF%] [errlen=%ERROR_LENGTH,userlen=%USER_LENGTH])
                            call bigecho "%ANSI_COLOR_ALARM%%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] ENV VAR ERROR!! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%ansi_color_normal%"
                            rem Output the updated ERROR_MESSAGE
                            %COLOR_ALARM%       
                            rem The warning right before 
                            echos %ERROR_MESSAGE%  
                            %COLOR_NORMAL% 
                            echo.
                            if "%USER_MESSAGE%" != "" (
                                REM Although this is technically advice, we 
                                REM are coloring it warning-style because 
                                REM advice related to an error in this context
                                REM pretty much *DOES* mean a warning in the 
                                REM outer context of our calling script, and 
                                REM that level of importance shoudln’t be as 
                                REM easily visually discarded as the advice 
                                REM color might usually be, because it’s more
                                REM important than simply advice -- 
                                REM      -- it represents a system failure!!!
                                REM ...so let’s put asterisks around it, too!
                                call warning "%@UNQUOTE[%USER_MESSAGE%]"
                            )
                                
                            %COLOR_ALARM%  %+ echos %ERROR_MESSAGE% %+ %COLOR_NORMAL% %+ echo. %+ rem right after
                            call bigecho "%ANSI_COLOR_ALARM%%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] ENV VAR ERROR!!! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%ansi_color_normal%"
                            eset %varname


                            rem Optional message as 2nd parameter for validate-environment-variablE  {singular} 
                            rem                           but NOT for validate-environment-variableS { plural }:
                                    iff  defined  PARAM2  .and.  not defined  %PARAM2%  then
                                        call warning "%PARAM2"
                                        rem  about to bigecho "%ANSI_COLOR_WARNING%%italics_on%%@unquote[%PARAM2]%italics_off% is not defined!"
                                        call          bigecho "%ANSI_COLOR_WARNING%%italics_on%%@unquote[%PARAM2]%italics_off% is not defined! ... set it?"
                                        *eset %PARAM2%
                                        call warning "%PARAM2"
                                    endiff


                            REM call alarm-beep     %+ REM was too annoying for the severity of the corresponding situations
                            call white-noise 1      %+ REM reduced to 2 seconds, then after a year or few, reduced to 1 second
                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%
                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%
                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%
                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%
                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%

                                         call exit-maybe

                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%
                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%
                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%
                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%
                            REM %COLOR_PROMPT% %+ pause %+ %COLOR_NORMAL%
                        goto :END


        ::::: ADDITIONALLY, VALIDATE THAT IT EXISTS, IF IT SEEMS TO BE POINTING TO A FOLDER/FILE:
                :Defined_YES
                if "%[%VARNAME%]" !=  "" set VARVALUE=%[%VARNAME%]
                rem echo [1] VARVALUE==`%[%VARNAME]`==`%[`%VARNAME%]==“%VARVALUE%”
                if %DEBUG_VALIDATE_ENV_VAR% eq 1  (echo %DEBUGPREFIX%VARNAME is %lq%%VARNAME%%rq%, VARVALUE (`%[%VARNAME%]`) is %lq%%VARVALUE%%rq% )
                iff ":\" == "%@INSTR[1,2,%VARVALUE%]" .or. ":/" == "%@INSTR[1,2,%VARVALUE%]" then
                        set VARVALUEDRIVE=%@INSTR[0,1,%VARVALUE%])     
                endiff


                set IS_FILE_LOCATION=0
                setdos /x-5
                iff defined VARVALUE then
                                                    
                        if %DEBUG_VALIDATE_ENV_VAR% eq 1  (echo VARVALUE is defined and is [%VARVALUE%], varname is %VARNAME 🐐rem>nul)
                        
                        rem It’s definitely NOT a file location if:
                        rem     1) The variable’s  name is “newline” or “tab”
                        rem     2) The variable’s value is “ ”
                        rem     3) The variable’s value does not contain a “.”

                        rem It definitely IS a file location if:
                        rem     1) The filename has “c:\” or some other drive letter at the beginning
                        rem     1) The filename ends in one of the extensions mentioned in FILEMASK_ALL_REGEX

                        
                        setdos /x-5
                        iff "%VARNAME%" == "newline" .or. "%VARNAME%" == "tab" .or. "%VARVALUE%" == " " .or. "%@RegEx[\.,%varvalue%]" != "1" then
                                set IS_FILE_LOCATION=0
                        elseiff "1" == "%@REGEX[^[A-Za-z]:[\\\/],%@UPPER[%@UNQUOTE[%VARVALUE%]]]"  .or.  "1" == "%@REGEX[%@UPPER[%FILEMASK_ALL_REGEX%]$,%@UPPER[%@UNQUOTE[%VARVALUE%]]]" then
                                rem if it ends with any file extension of commonly used files:
                                set IS_FILE_LOCATION=1
                        else                                
                                set IS_FILE_LOCATION=0
                        endiff       
                        setdos /x0
            rem else
                        rem [2B] or are We here? 🐐
            rem endiff                          
            :skippy

        setdos /x0

        rem echo IS_FILE_LOCATION=%IS_FILE_LOCATION% 🐐🐐

        if "0" == "%IS_FILE_LOCATION%" .or. "0" == "%@READY[%VARVALUEDRIVE%]" .or. 1 eq  %SKIP_VALIDATION_EXISTENCE%                      (goto :DontValidateIfExists)                         %+ rem //Don’t look for if we want to validate the variable only
        if exist "%VARVALUE%"          .or. isdir "%VARVALUE%"                                                                            (goto :ItExistsAfterall)                             %+ rem //Does it exist as a file or folder?
        if exist "%VARVALUE%.dep"      .or. isdir "%VARVALUE%.dep"  .or. exist "%VARVALUE%.deprecated" .or. isdir "%VARVALUE%.deprecated" (goto :ItExistsAfterall %+ gosub :ItIsDeprecated)    %+ rem //Internal kludge for the way I do workflows

        rem echo Doesn’t seem to exist ... 🐐🐐

        ::::: SET ERROR FLAGS (store error specifics for debugging analysis):
                set ERROR=1
                set ERROR_ENVIRONMENT_VALIDATION_FAILED=1
                SET ERROR_ENVIRONMENT_VALIDATION_FAILED_NAME=%VARNAME%
                SET ERROR_ENVIRONMENT_VALIDATION_FAILED_VALUE=%VARNVALUE%
                
        ::::: LET USER KNOW OF ERROR:
                REM without messaging system:
                    REM %COLOR_ALARM%   %+ echos * Environment variable %@UPPER[%VARNAME%] appears to be a file location that does not exist: %VARVALUE%
                    REM %COLOR_NORMAL%  %+ echo. %+ call white-noise 1
                    REM %COLOR_SUBTLE%  %+ *pause
                    REM %COLOR_NORMAL%
                    
                REM with messaging system:
                if "%USER_MESSAGE%" == "" goto :no_user_message
                                REM Although this is technically advice, we 
                                REM are coloring it warning-style because 
                                REM advice related to an error in this context
                                REM pretty much *DOES* mean a warning in the 
                                REM outer context of our calling script, and 
                                REM that level of importance shoudln’t be as 
                                REM easily visually discarded as the advice 
                                REM color might usually be, because it’s more
                                REM important than simply advice -- 
                                REM      -- it represents a system failure!!!
                                REM ...so let’s put asterisks around it, too!
                                rem call warning %USER_MESSAGE%
                                if %_column gt 0 echo.
                                echo %ANSI_COLOR_WARNING% %EMOJI_WARNING% %USER_MESSAGE% %ANSI_COLOR_NORMAL%
                :no_user_message

                rem echo [3] 🐐🐐
                    
                set old=%PRINTMESSAGE_OPT_SUPPRESS_AUDIO%
                set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=1

                iff "" != "%our_caller%" then
                        if %_column gt 0 echo.
                        echo %ANSI_COLOR_WARNING% %EMOJI_WARNING% dir/folder: %italics_on%%[_CWD]%italics_off% %ANSI_COLOR_NORMAL%    %@CHAR[55357]%@CHAR[56542]   ERROR IN: %blink_on%%italics_on%%@NAME[%our_caller%].%@EXT[%our_caller%]%italics_off%%blink_off% %ansi_color_normal%
                endiff

                if %_column gt 0 echo.
                echo %ANSI_COLOR_WARNING% %EMOJI_WARNING% dir/folder: %italics_on%%[_CWD]%italics_off% %ANSI_COLOR_NORMAL%

                rem TCCv33 introduced a new command. We tried it out like this:
                rem SET OUR_CALLER=%@execSTR[caller]
                rem if "" != "%OUR_CALLER%" call warning "%@CHAR[55357]%@CHAR[56542] Called by: %OUR_CALLER%"
                rem But it typically just told us that validate-environment-variable was being called by validate-environment-variables....not very useful

                rem Not very useful since it’s the params to this folder: call     warning  "    %@CHAR[55357]%@CHAR[56542] Parameters: %italics_on%%italics_on%%VEVPARAMS%%italics_off%%italics_off%" 

                set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=%old%
                iff "" != "%USER_MESSAGE%" then
                        unset /q indentation
                        if "%type%" == "FATAL_ERROR" set indentation=                 ``
                        set USER_MESSAGE_TO_USE= ... %user_message%
                else
                        unset /q USER_MESSAGE_TO_USE
                endiff
                if %_column gt 0 echo.
                echo %ansi_color_debug%DEBUG: varname = %VARNAME%, varvalue = %VARVALUE%%ansi_color_normal%
                set msg=%left_quote%%italics_on%%@UPPER[%VARNAME%]%italics_off%%right_quote% location does not exist: %left_quote%%VARVALUE%%right_quote%%USER_MESSAGE_TO_USE%%ANSI_COLOR_FATAL_ERROR%
                rem echo %ansi_color_fatal_error% %msg% %ansi_color_normal%
                setdos /x0
                rem @echo path is %path%
                rem dir  c:\bat\fatal_error.bat
                rem @echo %%@search[fatal_error.bat] is '%@search[fatal_error.bat]'
                if %_column gt 0 echo.
                call less_important "Calling script == “%our_caller%”"
                call c:\bat\fatal_error.bat "%msg%"
                call exit-maybe
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :ItIsDeprecated
            rem //Internal kludge for the way I do workflows.
            rem //WHICH IS: If "a.dep" or "a.deprecated" then I consider "a" to exist even if it doesn’t. Don’t ask.
            rem //When this happens, we display notification, with a custom sound effect,
            rem //but in a pleasant color, and less harsh sound effect, because this isn’t an error,
            rem //just something that we want to pay extra attention to vs business-as-usual.

            echo. %+ echo. %+ echo.
            %COLOR_ADVICE%
                echo %@CHAR[11088]%@CHAR[0] Environment variable %@UPPER[%VARNAME%] points deprecated file:
                echo            "%VARVALUE%"
            %COLOR_NORMAL%

            beep 73 3
            beep 73 2                  %+ REM //Our custom sound
            beep 73 1
            *pause
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :save_cusor_position []
                set vev_saved_row=%_row
                set vev_saved_col=%_column
                echos %ansi_cursor_invisible%
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :restore_cusor_position []
                echos %ansi_cursor_invisible%
                echos %@ansi_move_to_row[%@EVAL[%vev_saved_row% + 1]]
                echos %@ansi_move_to_col[%@EVAL[%vev_saved_col% + 1]]
                echos %ansi_cursor_invisible%
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :display_temp_output [varname]
                rem Alternating italics give it a little “jiggle” in its dance:
                        iff defined italics_maybe then
                                if "%italics_maybe%" == "%italics_on%" (
                                        set italics_maybe=%italics_off%
                                ) else ( 
                                        set italics_maybe=%italics_on%
                                )
                        endiff

                set coloring=%@randfg_soft[]
                echos %ansi_cursor_invisible%
                echos %@randfg_soft[]
                if defined italics_maybe echos %italics_maybe%  %+ rem Alternating italics give it a little “jiggle” in its dance:
                echos %@CHAR[9733] Validating variable: %@randfg_soft[]
                if defined varname echos %VARNAME%
                echos %@randfg_soft[]...%ansi_erase_to_eol%
                echos %@randfg_soft[]
                echos %ansi_cursor_invisible%
                set temp_output_vev_length=%@EVAL[26 + %@LEN[%VARNAME%]]
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



:Past_The_End_Of_The_Subroutines
:::::::::::::::::::::::::::::::::::::::::::::::::::::::

:ItExistsAfterall
:DontValidateIfExists
:END
        if "" == "%LAST_TITLE%" (set LAST_TITLE=TCC)
        title %LAST_TITLE%
        if defined        CURSOR_RESET echos %CURSOR_RESET%
        if defined ANSI_CURSOR_VISIBLE .and. "1" != "%VALIDATE_MULTIPLE%" echos %ANSI_CURSOR_VISIBLE%
        if defined ANSI_COLOR_RESET    echos %ANSI_COLOR_RESET%
        setdos /x0
        rem why won’t this work for this bat? endlocal LAST_TITLE ENVIRONMENT_VALIDATION_FAILED ENVIRONMENT_VALIDATION_FAILED_NAME ENVIRONMENT_VALIDATION_FAILED_VALUE DEBUG_VALIDATE_ENV_VAR DEBUG_NORMALIZE_MESSAGE ERROR ERROR_MESSAGE ERROR ERROR_ENVIRONMENT_VALIDATION_FAILED ERROR_ENVIRONMENT_VALIDATION_FAILED_NAME ERROR_ENVIRONMENT_VALIDATION_FAILED_VALUE

rem Erase temp output:
        iff "1" != "%any_env_var_validations_failed%" then
                gosub restore_cusor_position
                echos %@REPEAT[ ,%temp_output_vev_length%]``
                gosub restore_cusor_position
        endiff



