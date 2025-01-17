@loadbtm on
@if %DEBUG_TCASE gt 0 @echo %0 called by %_PBATCHNAME
@Echo off
@on break cancel
@setdos /x0

::::: GET PARAMETERS:
    set LAST_TITLE=%_TITLE
    set VEVPARAMS=%1$
    set PLUGIN_NAME=%1      
    set PARAM2=%2
    set PARAM3=%3
    set USER_MESSAGE=%2$
    if %DEBUG_VALIDATE_PLUGIN% eq 1 (echoerr %DEBUGPREFIX% if defined %PLUGIN_NAME% goto :Loaded_YES)
    set LAST_TITLE=%_WINTITLE
    title %0

:USAGE:  call validate-plugin PLUGIN_NAME_WITH_NO_PERCENTS     [a custom error message] 
:USAGE:       where option can be:
:USAGE:                             "some error message"        to be additional information provided to user if there is an error

:REQUIRES: exit-maybe.bat, warning.bat, fatalerror.bat, white-noise.bat (optional), bigecho.bat (optional)
:                                       REM car.bat, nocar.bat removed from requires 20230825


::::: DEBUG STUFFS:
    rem echoerr %ANSI_COLOR_DEBUG% %0 called with 1=%1, 2=%2, PLUGIN_NAME=%PLUGIN_NAME%, VEVPARAMS=%VEVPARAMS% %ANSI_COLOR_RESET%


::::: CLEAR LONGTERM ERROR FLAGS:
    set DEBUG_VALIDATE_PLUGIN=0
    set DEBUG_NORMALIZE_MESSAGE=0

::::: CLEAR LONGTERM ERROR FLAGS:
    set PLUGIN_VALIDATION_FAILED=0
    set PLUGIN_VALIDATION_FAILED_NAME=
    set PLUGIN_VALIDATION_FAILED_VALUE=
    set DEBUGPREFIX=- {validate-plugin} * ``

::::: VALIDATE PARAMETERS STRICTLY
    rem call debug "param3            is %param3%"
    rem call debug "validate_multiple_plugins is %validate_multiple_plugins%"
    rem call debug "about to check if PARAM3 [%param3%] ne '' .and. VALIDATE_MULTIPLE_PLUGINS [%VALIDATE_MULTIPLE_PLUGINS] ne 1 .... ALL_PARAMS is: %VEVPARAMS%"
    if "%_PBATCHNAME" == "validate-plugins.bat" set VALIDATE_MULTIPLE_PLUGINS=1
    iff "%PARAM3%" != "" .and. %VALIDATE_MULTIPLE_PLUGINS ne 1 then
        call bigecho "%ANSI_COLOR_ALARM%%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] PLUGIN ERROR! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]"
        color bright white on red
        echoerr  We can’t be passing a %italics%%blink%third%blink_off%%italics_off% parameter to %0
        echoerr  %underline%Did you mean%underline_off%: %italics%%0%double_underline%%blink%s%blink_off%%double_underline_off% %VEVPARAMS%%italics_off% 
        echoerr                                   (with an %left_quote%s%right_quote% after %left_quote%%italics%plugin%italics_off%%right_quote%)  ????

        call exit-maybe
        if %FORCE_EXIT eq 1 (goto :END)
        
        set VP_COMMENT=repeat 4 beep
        set VP_COMMENT=repeat 25 *pause

        goto :END
    endiff

    rem set SKIP_VALIDATION_EXISTENCE=0
    rem if "%PARAM2%" == "skip_validation_existence" .or. "%PARAM2%" == "skip_existence_validation" .or. "%PARAM2%" == "skip_validation" (
    rem    set SKIP_VALIDATION_EXISTENCE=1 
    rem    set USER_MESSAGE=%3$
    rem )
    if %DEBUG_NORMALIZE_MESSAGE eq 1 (echoerr %left_quote%%ansi_color_debug%%right_quote%- DEBUG: PARAM2: %left_quote%%PARAM2%%left_quote%%ansi_color_normal%right_quote%)


    iff %VALIDATE_MULTIPLE_PLUGINS ne 1 then
        gosub validate_plugin %PLUGIN_NAME%

        rem If this script gets aborted, leaving this flag set can create false errors:
                unset /q VALIDATE_MULTIPLE_PLUGINS 
    else 
        set USER_MESSAGE=
        do i = 1 to %# (
                 gosub validate_plugin  %[%i]
        )
    endiff





:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
goto :Past_The_End_Of_The_SubRoutines


    :validate_plugin [PLUGIN_NAME]
        rem debug: echoerr validate_plugin %PLUGIN_NAME%
        rem echoserr %@RANDCURSOR[]
        ::::: ACTUALLY SEE IF IT THE PLUGIN IS LOADED:
            if "" != "%@PLUGIN[%PLUGIN_NAME%]" (goto :Loaded_YES)
            if "" ==          "%PLUGIN_NAME%"  (goto :Loaded_NO )

                    ::::: REPOND IF IT IS NOT:
                        :Loaded_NO
                            set ERROR=1
                            set ERROR_MESSAGE=%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] Plugin %lq%%underline%%italics%%blink%%PLUGIN_NAME%%italics_off%%blink_off%%underline_off%%rq% is %double_Underline%not%double_Underline_off% loaded, and needs to be, in %italics_on%%lq%%[_PBATCHNAME]%rq%%italics_off%!!! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]
                            if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echoerr - DEBUG: ERROR_MESSAGE[1]: %ERROR_MESSAGE% [length_diff=%LENGTH_DIFF%] [errlen=%ERROR_LENGTH,userlen=%USER_LENGTH])
                            if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echoerr - DEBUG: `%`USER_MESSAGE`%` is %lq%%USER_MESSAGE%%rq%)
                            if "%USER_MESSAGE%" != "" goto :Do_It_1
                                                      goto :Do_It_1_Done
                            :Do_It_1
                                REM Normalize width of ERROR_MESSAGE to be same width as USER_MESSAGE
                                if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echoerr - DEBUG: User message found)

                                rem Get the length of both
                                set "ERROR_LENGTH=%@LEN[%ERROR_MESSAGE]"
                                set  "USER_LENGTH=%@LEN[%USER_MESSAGE%]"

                                rem Calculate the difference in length
                                set /a "LENGTH_DIFF=!USER_LENGTH! - !ERROR_LENGTH!"

                                REM for /L %%i in (1,1,%LENGTH_DIFF%) do (set EXCLAMATION_MARKS=%EXCLAMATION_MARKS%!)
                                REM 
                                REM rem Substitute the final sequence of exclamation marks in ERROR_MESSAGE
                                REM if DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echoerr - DEBUG: EXCLAMATION_MARKS is “%EXCLAMATION_MARKS%%rq%)
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
                            if %DEBUG_NORMALIZE_MESSAGE eq 1 (%COLOR_DEBUG% %+ echoerr ERROR_MESSAGE[2]: %ERROR_MESSAGE% [length_diff=%LENGTH_DIFF%] [errlen=%ERROR_LENGTH,userlen=%USER_LENGTH])
                            call bigecho "%ANSI_COLOR_ALARM%%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] PLUGIN ERROR!! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%ansi_color_normal%"
                            rem Output the updated ERROR_MESSAGE
                            %COLOR_ALARM%       
                            rem The warning right before 
                            echoserr %ERROR_MESSAGE%  
                            %COLOR_NORMAL% 
                            echoerr.
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
                                
                            %COLOR_ALARM%  %+ echoserr %ERROR_MESSAGE% %+ %COLOR_NORMAL% %+ echoerr. %+ rem right after
                            call bigecho "%ANSI_COLOR_ALARM%%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0] PLUGIN ERROR!!! %@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%@CHAR[11088]%@CHAR[0]%ansi_color_normal%"


                            rem Optional message as 2nd parameter for validate-plugin  {singular} 
                            rem                           but NOT for validate-plugins { plural }:
                                    iff  defined  PARAM2  .and.  not defined  %PARAM2%  then
                                        call warning "%PARAM2"
                                        rem  about to bigecho "%ANSI_COLOR_WARNING%%italics_on%%@unquote[%PARAM2]%italics_off% is not defined!"
                                        call          bigecho "%ANSI_COLOR_WARNING%%italics_on%%@unquote[%PARAM2]%italics_off% is not defined!"
                                        call warning "%PARAM2"
                                    endiff


                            REM call alarm-beep     %+ REM was too annoying for the severity of the corresponding situations
                            call white-noise 1      %+ REM reduced to 2 seconds, then after a year or few, reduced to 1 second

                            call exit-maybe
                        goto :END


            :skippy

        setdos /x0

        ::::: SET ERROR FLAGS (store error specifics for debugging analysis):
                set ERROR=1
                set ERROR_PLUGIN_VALIDATION_FAILED=1
                SET ERROR_PLUGIN_VALIDATION_FAILED_NAME=%PLUGIN_NAME%
                
        ::::: LET USER KNOW OF ERROR:
                REM with messaging system
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
                    call     warning  "    %@CHAR[55357]%@CHAR[56542]   ERROR IN: %blink_on%%italics_on%%[_pbatchname]%italics_off%%blink_off%"      
                    call     warning  "    %@CHAR[55357]%@CHAR[56542] Dir/Folder: %italics_on%%[_CWD]%italics_off%"              
                    call     warning  "    %@CHAR[55357]%@CHAR[56542] Parameters: %italics_on%%italics_on%%VEVPARAMS%%italics_off%%italics_off%" 
                    set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=%old%
                    iff "%USER_MESSAGE%" != "" then
                        set USER_MESSAGE_TO_USE=%NEWLINE%%USER_MESSAGE%
                    else
                        set USER_MESSAGE_TO_USE=
                    endiff
                    call fatal_error "%left_quote%%italics_on%%@UPPER[%PLUGIN_NAME%]%italics_off%%right_quote% plugin is not installed: %left_quote%(UNKNOWN)%right_quote%...%USER_MESSAGE_TO_USE%%ANSI_COLOR_FATAL_ERROR%" 
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



:Past_The_End_Of_The_SubRoutines
:::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
:Loaded_YES
if "" == "%LAST_TITLE%" (set LAST_TITLE=TCC)
title %LAST_TITLE%

echos %CURSOR_RESET%
setdos /x0
