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

::::: VALIDATE PARAMETERS STRICTLY
    rem call debug "param3            is %param3%"
    rem call debug "validate_multiple is %validate_multiple%"
    rem call debug "about to check if PARAM3 [%param3%] ne '' .and. VALIDATE_MULTIPLE [%VALIDATE_MULTIPLE] ne 1 .... ALL_PARAMS is: %VEVPARAMS%"
    iff "%PARAM3%" ne "" .and. %VALIDATE_MULTIPLE ne 1 then
        call bigecho "%ANSI_COLOR_ALARM%%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] ENV VAR ERROR! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]"
        color bright white on red
        echo  We can't be passing a %italics%%blink%third%blink_off%%italics_off% parameter to validate-environment-variable.bat 
        echo  %underline%Did you mean%underline_off%: %italics%validate-environment-variable%double_underline%%blink%s%blink_off%%double_underline_off% %VEVPARAMS%%italics_off% 
        echo                                   (with an 's' after '%italics%variable%italics_off%')  ????

        call exit-maybe
        if %FORCE_EXIT eq 1 (goto :END)
        
        set VEV_COMMENT=repeat 4 beep
        set VEV_COMMENT=repeat 25 *pause

        goto :END
    endiff

    set SKIP_VALIDATION_EXISTENCE=0
    if "%PARAM2%" eq "skip_validation_existence" .or. "%PARAM2%" eq "skip_existence_validation" .or. "%PARAM2%" eq "skip_validation" (
        set SKIP_VALIDATION_EXISTENCE=1 
        set USER_MESSAGE=%3$
    )
    if %DEBUG_NORMALIZE_MESSAGE eq 1 (echo %ansi_color_debug%- DEBUG: PARAM2: '%PARAM2%'%ansi_color_normal%)


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
goto :Past_The_End_Of_The_Sub-Routines


    :validate_environment_variable [VARNAME]
        rem debug: echo validate_environment_variable %varname%
        rem echos %@RANDCURSOR[]
        ::::: SEE IF IT IS DEFINED:
            if defined %VARNAME% (goto :Defined_YES)
            if ""  eq  %VARNAME% (goto :Defined_NO )

                    ::::: REPOND IF IT IS NOT:
                        :Defined_NO
                            set ERROR=1
                            set ERROR_MESSAGE=%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] Environment variable '%underline%%italics%%blink%%varname%%italics_off%%blink_off%%underline_off%' is %double_Underline%not%double_Underline_off% defined, and needs to be, in %italics_on%'%[_PBATCHNAME]'%italics_off%!!! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]
                            if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo - DEBUG: ERROR_MESSAGE[1]: %ERROR_MESSAGE% [length_diff=%LENGTH_DIFF%] [errlen=%ERROR_LENGTH,userlen=%USER_LENGTH])
                            if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo - DEBUG: `%`USER_MESSAGE`%` is '%USER_MESSAGE%')
                            if "%USER_MESSAGE%" ne "" goto :Do_It_1
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
                                REM if DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo - DEBUG: EXCLAMATION_MARKS is '%EXCLAMATION_MARKS%')
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
                            if "%USER_MESSAGE%" ne "" (
                                REM Although this is technically advice, we 
                                REM are coloring it warning-style because 
                                REM advice related to an error in this context
                                REM pretty much *DOES* mean a warning in the 
                                REM outer context of our calling script, and 
                                REM that level of importance shoudln't be as 
                                REM easily visually discarded as the advice 
                                REM color might usually be, because it's more
                                REM important than simply advice -- 
                                REM      -- it represents a system failure!!!
                                REM ...so let's put asterisks around it, too!
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
                rem @echo on
                        rem  echo VARVALUE is [%VARVALUE%], varname is %VARNAME>nul
                        rem  ************************** "1" eq "%@REGEX[^[A-Za-z]:,%@UPPER[@UNQUOTE[%VARVALUE%]]]" then
                        echo ************************** "1" eq "%@REGEX[^[A-Za-z]:,@UPPER[@UNQUOTE[%VARVALUE%]]]" then>nul
                        setdos /x-5
                        iff "%VARVALUE%" eq " " then
                                set IS_FILE_LOCATION=0
                                goto :skippy
                        endiff                                
                        rem echo 🧟🏻‍♀️ if "1" eq "%@REGEX[^[A-Za-z]:[\\\/],%@UPPER[%@UNQUOTE[%VARVALUE%]]]"       set IS_FILE_LOCATION=1 >nul
                        iff "%VARNAME%" eq "newline" .or. "%VARNAME%" eq "tab" then
                                rem It's not something we want in regexes, so skip this next part
                                rem Idea: we *could* skip any string which doesn't have a . in it. Safe but slightly destructive.
                        else                                
                                if "1" eq "%@REGEX[^[A-Za-z]:[\\\/],%@UPPER[%@UNQUOTE[%VARVALUE%]]]"  .or.  "1" eq "%@REGEX[%@UPPER[%FILEMASK_ALL_REGEX%]$,%@UPPER[%@UNQUOTE[%VARVALUE%]]]" (set IS_FILE_LOCATION=1) %+ rem if it ends with any file extension of commonly used files
                        endiff       
                        setdos /x0
                @echo off                        
            endiff                          
            :skippy

        setdos /x0
        if  "0" eq "%IS_FILE_LOCATION%"         (goto :DontValidateIfExists)
        if  "0" eq "%@READY[%VARVALUEDRIVE%]"   (goto :DontValidateIfExists)                         %+ rem //Don't look for if drive letter doesn't exist--it's SLOWWWWW
        if   1  eq  %SKIP_VALIDATION_EXISTENCE% (goto :DontValidateIfExists)                         %+ rem //Don't look for if we want to validate the variable only
        if exist "%VARVALUE%"                   (                         goto :ItExistsAfterall)    %+ rem //Does it exist as a file?
        if isdir "%VARVALUE%"                   (                         goto :ItExistsAfterall)    %+ rem //Does it exist as a folder?
        if exist "%VARVALUE%.dep"               (gosub :ItIsDeprecated %+ goto :ItExistsAfterall)    %+ rem //Internal kludge for the way I do workflows
        if isdir "%VARVALUE%.dep"               (gosub :ItIsDeprecated %+ goto :ItExistsAfterall)    %+ rem //Internal kludge for the way I do workflows
        if exist "%VARVALUE%.deprecated"        (gosub :ItIsDeprecated %+ goto :ItExistsAfterall)    %+ rem //Internal kludge for the way I do workflows
        if isdir "%VARVALUE%.deprecated"        (gosub :ItIsDeprecated %+ goto :ItExistsAfterall)    %+ rem //Internal kludge for the way I do workflows

        ::::: SET ERROR FLAGS (store error specifics for debugging analysis):
                set ERROR=1
                set ERROR_ENVIRONMENT_VALIDATION_FAILED=1
                SET ERROR_ENVIRONMENT_VALIDATION_FAILED_NAME=%VARNAME%
                SET ERROR_ENVIRONMENT_VALIDATION_FAILED_VALUE=%VARNVALUE%
        ::::: LET USER KNOW OF ERROR:
                REM without messaging system
                    REM %COLOR_ALARM%   %+ echos * Environment variable %@UPPER[%VARNAME%] appears to be a file location that does not exist: %VARVALUE%
                    REM %COLOR_NORMAL%  %+ echo. %+ call white-noise 1
                    REM %COLOR_SUBTLE%  %+ *pause
                    REM %COLOR_NORMAL%
                REM with messaging system
                    iff "%USER_MESSAGE%" ne "" then
                        REM Although this is technically advice, we 
                        REM are coloring it warning-style because 
                        REM advice related to an error in this context
                        REM pretty much *DOES* mean a warning in the 
                        REM outer context of our calling script, and 
                        REM that level of importance shoudln't be as 
                        REM easily visually discarded as the advice 
                        REM color might usually be, because it's more
                        REM important than simply advice -- 
                        REM      -- it represents a system failure!!!
                        REM ...so let's put asterisks around it, too!
                        call warning %USER_MESSAGE%
                    endiff
                    call     warning  " Called by: %_pbatchname" silent
                    call     warning  "Parameters: %italics_on%%VEVPARAMS%%italics_off%" silent
                    call     warning  "       CWP: %_CWP" silent
                    call fatal_error "'%italics_on%%@UPPER[%VARNAME%]%italics_off%' location does not exist: '%VARVALUE%'...%ANSI_COLOR_WARNING%%USER_MESSAGE%%ANSI_COLOR_FATAL_ERROR%" silent
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :ItIsDeprecated
            rem //Internal kludge for the way I do workflows.
            rem //WHICH IS: If "a.dep" or "a.deprecated" then I consider "a" to exist even if it doesn't. Don't ask.
            rem //When this happens, we display notification, with a custom sound effect,
            rem //but in a pleasant color, and less harsh sound effect, because this isn't an error,
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




:Past_The_End_Of_The_Sub-Routines
:::::::::::::::::::::::::::::::::::::::::::::::::::::::

:ItExistsAfterall
:DontValidateIfExists
:END
if "" eq "%LAST_TITLE%" (set LAST_TITLE=TCC)
title %LAST_TITLE%

echos %CURSOR_RESET%
setdos /x0
