@loadbtm on
@Echo off
@on break cancel
@setdos /x0


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

::::: CLEAR LONGTERM ERROR FLAGS:
    set ENVIRONMENT_VALIDATION_FAILED=0
    set ENVIRONMENT_VALIDATION_FAILED_NAME=
    set ENVIRONMENT_VALIDATION_FAILED_VALUE=
    set DEBUGPREFIX=- {validate-environment-variable} * ``
    
::::: GET CALLING-BAT-FILE INFO, INCLUDING THAT MANUALLY PASSED FROM GRANDPARENT BATCH FILE:
        set OUR_CALLER=%_PBATCHNAME
        if "%_PBATCHNAME" == "%bat%\validate-environment-variables.bat" .and. defined PBATCH2 (set OUR_CALLER=%PBATCH2%)
        set OUR_CALLER=%@NAME[%our_caller].%@EXT[%our_caller]
    
::::: VALIDATE ENVIRONMENT:
        iff not defined FILEMASK_ALL_REGEX then
                %color_warning%
                echo WARNING in validate-environment-variable.bat when called by %OUR_CALLER%: FILEMASK_ALL_REGEX not defined!
                if defined PBATCH2 echo       grandparent BAT = %PBATCH2%
                pause
                goto :END
        endiff


::::: VALIDATE PARAMETERS STRICTLY
    rem call debug "param3            is %param3%"
    rem call debug "validate_multiple is %validate_multiple%"
    rem call debug "about to check if PARAM3 [%param3%] ne '' .and. VALIDATE_MULTIPLE [%VALIDATE_MULTIPLE] ne 1 .... ALL_PARAMS is: %VEVPARAMS%"
    if "%@NAME[%OUR_CALLER%]" == "validate-environment-variables" set VALIDATE_MULTIPLE=1
    iff "%PARAM3%" != "" .and. %VALIDATE_MULTIPLE ne 1 then
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
    if %DEBUG_NORMALIZE_MESSAGE eq 1 (echo %ansi_color_debug%- DEBUG: PARAM2: %left_quotes%%PARAM2%%right_quotes%%ansi_color_normal%)


    iff %VALIDATE_MULTIPLE ne 1 then
        gosub validate_environment_variable %VARNAME%

        rem If this script gets aborted, leaving this flag set can create false errors:
                unset /q VALIDATE_MULTIPLE 
    else 
        set USER_MESSAGE=
        do i = 1 to %# (
                 gosub validate_environment_variable  %[%i]
        )
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


                            rem Optional message as 2nd parameter for validate-environment-variablE  {singular} 
                            rem                           but NOT for validate-environment-variableS { plural }:
                                    iff  defined  PARAM2  .and.  not defined  %PARAM2%  then
                                        call warning "%PARAM2"
                                        rem  about to bigecho "%ANSI_COLOR_WARNING%%italics_on%%@unquote[%PARAM2]%italics_off% is not defined!"
                                        call          bigecho "%ANSI_COLOR_WARNING%%italics_on%%@unquote[%PARAM2]%italics_off% is not defined!"
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
                set VARVALUE=%[%VARNAME%]``                    
                if %DEBUG_VALIDATE_ENV_VAR% eq 1 (echo %DEBUGPREFIX%VARVALUE is %VARVALUE%)
                set VARVALUEDRIVE=%@INSTR[0,1,%VARVALUE%])     


                set IS_FILE_LOCATION=0
                setdos /x-5
                iff defined VARVALUE then
                                                    
                        rem  echo VARVALUE is [%VARVALUE%], varname is %VARNAME>nul
                        
                        rem It’s definitely not a file location if:
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
            endiff                          
            :skippy

        setdos /x0
        if "0" == "%IS_FILE_LOCATION%" .or. "0" == "%@READY[%VARVALUEDRIVE%]" .or. 1 eq  %SKIP_VALIDATION_EXISTENCE%                      (goto :DontValidateIfExists)                         %+ rem //Don’t look for if we want to validate the variable only
        if exist "%VARVALUE%"          .or. isdir "%VARVALUE%"                                                                            (goto :ItExistsAfterall)                             %+ rem //Does it exist as a file or folder?
        if exist "%VARVALUE%.dep"      .or. isdir "%VARVALUE%.dep"  .or. exist "%VARVALUE%.deprecated" .or. isdir "%VARVALUE%.deprecated" (goto :ItExistsAfterall %+ gosub :ItIsDeprecated)    %+ rem //Internal kludge for the way I do workflows

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
                iff "%USER_MESSAGE%" != "" then
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
                                call warning %USER_MESSAGE%
                endiff
                    
                set old=%PRINTMESSAGE_OPT_SUPPRESS_AUDIO%
                set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=1

                if "" != "%our_caller%" call   warning  "    %@CHAR[55357]%@CHAR[56542]   ERROR IN: %blink_on%%italics_on%%@NAME[%our_caller%].%@EXT[%our_caller%]%italics_off%%blink_off%"      

                call warning "  dir/folder: %italics_on%%[_CWD]%italics_off%"              

                rem TCCv33 introduced a new command. We tried it out like this:
                rem SET OUR_CALLER=%@execSTR[caller]
                rem if "" != "%OUR_CALLER%" call warning "%@CHAR[55357]%@CHAR[56542] Called by: %OUR_CALLER%"
                rem But it typically just told us that validate-environment-variable was being called by validate-environment-variables....not very useful

                rem Not very useful since it’s the params to this folder: call     warning  "    %@CHAR[55357]%@CHAR[56542] Parameters: %italics_on%%italics_on%%VEVPARAMS%%italics_off%%italics_off%" 

                set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=%old%
                iff "" != "%USER_MESSAGE%" then
                        set USER_MESSAGE_TO_USE=%NEWLINE%%USER_MESSAGE%
                else
                        set USER_MESSAGE_TO_USE=
                endiff
                call fatal_error "%left_quote%%italics_on%%@UPPER[%VARNAME%]%italics_off%%right_quote% location does not exist: %left_quote%%VARVALUE%%right_quote%...%USER_MESSAGE_TO_USE%%ANSI_COLOR_FATAL_ERROR%" 
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




:Past_The_End_Of_The_Subroutines
:::::::::::::::::::::::::::::::::::::::::::::::::::::::

:ItExistsAfterall
:DontValidateIfExists
:END
if "" == "%LAST_TITLE%" (set LAST_TITLE=TCC)
title %LAST_TITLE%

echos %CURSOR_RESET%
setdos /x0
