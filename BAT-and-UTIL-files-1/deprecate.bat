@Echo Off
 on break cancel

:USAGE: To mark a folder or file as deprecated

set DEP_PARAM1=%1

if "%2" ne "force" (call validate-environment-variable DEP_PARAM1 "First parameter must be a file that exists")

set                              NOQUOTES=%@STRIP[%=",%DEP_PARAM1]
set        LAST_FILE_DEPPED_OLD=%NOQUOTES%
set        LAST_FILE_DEPPED_NEW=%NOQUOTES.deprecated
set        LAST_FILE_DEPPED_NEW2=%NOQUOTES.%_DATETIME.deprecated

if exist "%LAST_FILE_DEPPED_NEW%" .and. "%@REGEX[\*,%LAST_FILE_DEPPED_NEW%]" eq "1" (%COLOR_ALARM% %+ echos LAST_FILE_DEPPED_NEW of %LAST_FILE_DEPPED_NEW% already exists and should not! Why could that be, hmmmmmm?? %+ %COLOR_NORMAL% %+ echo. %+ call white-noise 1)

set SUBCOMMAND=ren
iff isdir "%DEP_PARAM1" then
        set SUBCOMMAND=mv/ds 
        set LAST_FILE_DEPPED_NEW=%@STRIP[\,%LAST_FILE_DEPPED_NEW%]
endiff        

if exist "%LAST_FILE_DEPPED_NEW%" set LAST_FILE_DEPPED_NEW=%LAST_FILE_DEPPED_NEW2%

set REDOCOMMAND=%SUBCOMMAND% "%LAST_FILE_DEPPED_OLD%" "%LAST_FILE_DEPPED_NEW%"
set UNDOCOMMAND=call undep
   %REDOCOMMAND%

if exist "%LAST_FILE_DEPPED_OLD%" .and. "%@REGEX[\*,%LAST_FILE_DEPPED_OLD%]" eq "1" (echos %ANSI_COLOR_ALARM%LAST_FILE_DEPPED_OLD of %LAST_FILE_DEPPED_OLD% *still* exists and should not! Might want to run 'handles'.%ANSI_RESET% %+ echo. %+ call white-noise 1)

unset  /q  NOQUOTES
