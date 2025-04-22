@Echo Off
 on break cancel

:USAGE: To mark a folder or file as deprecated


rem Validate environment (once):
        if "2" != "%validated_deprecate%"
                call validate-in-path AskYN white-noise undep
                call validate-environment-variables color_alarm ansi_color_alarm lq rq color_normal italics_on italics_off
                set  validated_deprecate=1
        endiff

rem Validate parameters:
        set DEP_PARAM1=%1
        if "%2" != "force" (if not exist %DEP_PARAM1% call validate-environment-variable DEP_PARAM1 "First parameter must be a file that exists")

rem Massage parameters:
        set                              NOQUOTES=%@STRIP[%=",%DEP_PARAM1]
        set        LAST_FILE_DEPPED_OLD=%NOQUOTES%
        set        LAST_FILE_DEPPED_NEW=%NOQUOTES.deprecated
        set        LAST_FILE_DEPPED_NEW2=%NOQUOTES.%_DATETIME.deprecated

rem Make sure new-name isn’t coincidentally another file that already exists:
        iff exist "%LAST_FILE_DEPPED_NEW%" .and. "%@REGEX[\*,%LAST_FILE_DEPPED_NEW%]" eq "1" then
                           %COLOR_ALARM% 
                echos %ANSI_COLOR_ALARM%LAST_FILE_DEPPED_NEW of %lq%%LAST_FILE_DEPPED_NEW%%rq% already exists and should not! Why could that be, hmmmmmm?? 
                          %COLOR_NORMAL% 
                echo %ANSI_COLOR_NORMAL%. 
                call white-noise 1
        endiff

rem Check if we are dealing with a directory or with an individual file:
        set SUBCOMMAND=ren
        iff isdir "%DEP_PARAM1" then
                set SUBCOMMAND=mv/ds 
                set LAST_FILE_DEPPED_NEW=%@STRIP[\,%LAST_FILE_DEPPED_NEW%]
        endiff        


rem Check if filename.depcreated already exists, in which case we must use the more-unique filename that has the moment-in-time in it:
        if exist "%LAST_FILE_DEPPED_NEW%" set LAST_FILE_DEPPED_NEW=%LAST_FILE_DEPPED_NEW2%

rem Generate our redo and undo commands, then actually do it (by running the REDO command):
        set REDOCOMMAND=%SUBCOMMAND% "%LAST_FILE_DEPPED_OLD%" "%LAST_FILE_DEPPED_NEW%"
        set UNDOCOMMAND=call undep
           %REDOCOMMAND%


rem If the old file still exists, we’ve got issues:
        :recheck_51
        iff exist "%LAST_FILE_DEPPED_OLD%" .and. "%@REGEX[\*,%LAST_FILE_DEPPED_OLD%]" eq "1" then
                echos %ANSI_COLOR_ALARM%LAST_FILE_DEPPED_OLD of %lq%%LAST_FILE_DEPPED_OLD%%rq% *%italics_on%still%italics_off%* exists and should not! Might want to run '%italics_on%handles%italics_off%'.%ANSI_RESET% 
                echo. 
                call white-noise 1
                call askyn "delete “%italics_on%%LAST_FILE_DEPPED_OLD%%italics_off%”" yes 5000
                iff "Y" == "%ANSWER%" then
                        *del /z /a: /f /Ns "%LAST_FILE_DEPPED_OLD%"
                        goto /i recheck_51
                endiff
        endiff

rem Cleanup:
        unset /q  NOQUOTES


