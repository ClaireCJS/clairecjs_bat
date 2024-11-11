@Echo off
@on break cancel

::::: GET PARAMETERS:
    set VFUNCPARAMS=%1$
    set FUNCNAME=%1      
    set PARAM2=%2
    set PARAM3=%3
    set USER_MESSAGE=%2$
    if %DEBUG_VALIDATE_FUNCTION% eq 1 (echo %DEBUGPREFIX% if "%@FUNCTION[%FUNCNAME]" ne "" goto :Defined_YES)
    set LAST_TITLE=%_WINTITLE
    title %0

:USAGE:  call validate-function FUNCNAME_NO_PERCENT "some error message" 
:USAGE:       where option can be:
:USAGE:                             "some error message"        to be additional information provided to user if there is an error

:REQUIRES: exit-maybe.bat, warning.bat, fatalerror.bat, white-noise.bat (optional), bigecho.bat (optional)
:                                       REM car.bat, nocar.bat removed from requires 20230825


::::: DEBUG STUFFS:
    :echo %ANSI_COLOR_DEBUG% %0 called with 1=%1, 2=%2, FUNCNAME=%FUNCNAME%, VFUNCPARAMS=%VFUNCPARAMS% %ANSI_COLOR_RESET%
    :echo on


::::: CLEAR LONGTERM ERROR FLAGS:
    set DEBUG_VALIDATE_FUNCTION=0
    set DEBUG_NORMALIZE_MESSAGE=0

::::: CLEAR LONGTERM ERROR FLAGS:
    set ENVIRONMENT_VALIDATION_FAILED=0
    set ENVIRONMENT_VALIDATION_FAILED_NAME=validate-functions
    set ENVIRONMENT_VALIDATION_FAILED_VALUE=%*
    set DEBUGPREFIX=- {validate-function} * ``

::::: VALIDATE PARAMETERS STRICTLY
    rem call debug "param3            is %param3%"
    rem call debug "validate_multiple is %validate_multiple%"
    rem call debug "about to check if PARAM3 [%param3%] ne '' .and. VALIDATE_MULTIPLE [%VALIDATE_MULTIPLE] ne 1 .... ALL_PARAMS is: %VFUNCPARAMS%"
    if "%PARAM3%" ne "" .and. %VALIDATE_MULTIPLE ne 1 (
        call bigecho "%ANSI_COLOR_ALARM%*** ENV VAR ERROR! ***"
        color bright white on red
        echo  We can't be passing a %italics%%blink%third%blink_off%%italics_off% parameter to validate-function.bat 
        echo  %underline%Did you mean%underline_off%: %italics%validate-function%double_underline%%blink%s%blink_off%%double_underline_off% %VFUNCPARAMS%%italics_off% 
        echo                                   (with an 's' after '%italics%variable%italics_off%')  ????
        call exit-maybe
        
        set VFUNC_COMMENT=color white on black
        set VFUNC_COMMENT=beep
        set VFUNC_COMMENT=beep
        set VFUNC_COMMENT=beep
        set VFUNC_COMMENT=beep
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause
        set VFUNC_COMMENT=*pause

        goto :END
    )

    set SKIP_VALIDATION_EXISTENCE=0
    if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo - DEBUG: PARAM2: '%PARAM2%')


    if %VALIDATE_MULTIPLE ne 1 (
        gosub validate_function %FUNCNAME%
        rem If this script gets aborted, leaving this flag set can create false errors:
        unset /q VALIDATE_MULTIPLE 
    ) else (
        set USER_MESSAGE=
        do i = 1 to %# (
                 gosub validate_function  %[%i]
        )
    )





:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
goto :Past_The_End_Of_The_Sub_Routines


    :validate_function [FUNCNAME]
        rem debug: echo validate_function %FUNCNAME%
        ::::: SEE IF IT IS DEFINED:
            if "%@FUNCTION[%FUNCNAME]" ne "" (goto :Defined_YES)
            if             %FUNCNAME%  eq "" (goto :Defined_NO )

                    ::::: RESPOND IF IT IS NOT:
                        :Defined_NO
                            set ERROR=1
                            set ERROR_MESSAGE=*** Function '%underline%%italics%%blink%%FUNCNAME%%italics_off%%blink_off%%underline_off%' is %double_Underline%not%double_Underline_off% defined, and needs to be!!! ***
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

                                if %LENGTH_DIFF% lss 0 (
                                    set /a "LENGTH_DIFF=-%LENGTH_DIFF% / 2"
                                )
                                if %LENGTH_DIFF% lss 0 (
                                    rem If USER_MESSAGE is longer
                                    for /L %%i in (1,1,%LENGTH_DIFF%)    do   (set "ERROR_MESSAGE=*%ERROR_MESSAGE%*")
                                    if          %@EVAL[%LENGTH_DIFF % 2] == 0 (set "ERROR_MESSAGE=%ERROR_MESSAGE%*" )
                                ) else (
                                    rem If ERROR_MESSAGE is longer
                                    for /L %%i in (1,1,%LENGTH_DIFF%)    do   (set "USER_MESSAGE=*%USER_MESSAGE%*")
                                    if          %@EVAL[%LENGTH_DIFF % 2] == 0 (set "USER_MESSAGE=%USER_MESSAGE%*" )
                                )

                                rem Output the updated ERROR_MESSAGE
                                set ERROR_MESSAGE=%NORMALIZED_ERROR_MESSAGE%
                            :Do_It_1_Done
                            if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echo ERROR_MESSAGE[2]: %ERROR_MESSAGE% [length_diff=%LENGTH_DIFF%] [errlen=%ERROR_LENGTH,userlen=%USER_LENGTH])
                            call bigecho "%ANSI_COLOR_ALARM%*** ENV VAR ERROR! ***"
                            %COLOR_ALARM%       
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
                                
                            %COLOR_ALARM%  %+ echos %ERROR_MESSAGE% %+ %COLOR_NORMAL% %+ echo.
                            call bigecho "%ANSI_COLOR_ALARM%*** ENV VAR ERROR! ***"
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
            rem this is leftover code from validating file locations from validate-environment-variable.bat and not too germaine to things...
            rem set VARVALUE=%[%FUNCNAME%]``                    
            rem if %DEBUG_VALIDATE_FUNCTION% eq 1 (echo %DEBUGPREFIX%VARVALUE is %VARVALUE%)
            rem set VARVALUEDRIVE=%@INSTR[0,1,%VARVALUE%])     
            set ERROR=0
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
                echo * Environment variable %@UPPER[%FUNCNAME%] points deprecated file:
                echo            "%VARVALUE%"
            %COLOR_NORMAL%

            beep 73 3
            beep 73 2                  %+ REM //Our custom sound
            beep 73 1
            *pause
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:Past_The_End_Of_The_Sub_Routines
:::::::::::::::::::::::::::::::::::::::::::::::::::::::

:ItExistsAfterall
:DontValidateIfExists
:END
call fix-window-title

