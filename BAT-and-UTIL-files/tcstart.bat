@Echo off

rem major speedup by skipping this bat file for certain shells:
    IF "%_PIPE %_TRANSIENT" != "0 0" (call setpath %+ QUIT)




rem ::::: BAD IDEA, DON'T DO THIS, BECAUSE THIS HAPPENS MORE THAN YOU'D THINK:
    :*cls 
    :echo Running TCStart.btm...




rem ::::: OPTOINALLY FIX THE WINDOW SO NONE OF THE EXTRA TCMD DDOCKED STUFF EXISTS, LEAVING ONLY THE MAIN WINDOW:
    rem window restore


rem ::::: SET UP FOR ENVIRONMENT.BAT
    set OS=10
    SET MACHINENAME=DEMONA
    set LOGGING_LEVEL=None
    set MOST_SECONDS_TCC_WOULD_EVER_TAKE_TO_START_UP=6

rem ::::: RUN ENVIRONMENT.BAT, WITH THE ONE PRE-REQUISITE THAT THE MACHINE NAME IS SET:
    title TCC
    call c:\bat\environm.btm 










rem ::::::::::::::::::: ::::::::::::::::::: WINDOWS TERMINAL USHURED A NEED MORE MORE STARTUP LOGIC:  :::::::::::::::::::::::::::::::::::::: 


rem                     1) We had to create an autorun system for window splits so that we could use them efficiently.
rem                     2) We had to create a way to change folders automatically because windows terminal starts us
rem                        in %HOME% instead of where we were when we called it


rem ::::: IS THIS A SPLIT WINDOW? THEN OUR CONVENTION IS TO CHECK THIS FILE, AND RUN IT IF IT'S RELATIVELY FRESH
rem
rem        Some complications we've had to address:
rem           
rem        First, when we added the 'exit' option, if the command was a BAT file, it would never return to exit.
rem               * We addressed this by detecting the command using 'which', extracting the extension,
rem                 and if it is a BAT file, adding 'call' to the beginning.
rem           
rem        Secondly, if the command takes a long time to run, then if we attempt to do this concurrently,
rem                  we won't be able to create the BAT file because it is still running.
rem                  * We addressed this by renaming the script to a unique filename before running it.







            set                    AUTORUN_SCRIPT=c:\tcmd\runonce-post-split.bat
            if exist              %AUTORUN_SCRIPT% (
                call set-fileage  %AUTORUN_SCRIPT%
                if not exist      %AUTORUN_SCRIPT% goto :END
                set      NEWNAME=%[AUTORUN_SCRIPT]%_PID%_datetime.bat
                set AGE_THRESHOLD=%@EVAL[%MOST_SECONDS_TCC_WOULD_EVER_TAKE_TO_START_UP * 1.5]

                if not exist %AUTORUN_SCRIPT% goto :END

                if  %RESULT lt %AGE_THRESHOLD (
                    if not exist %AUTORUN_SCRIPT%  goto :END
                     ren   /q    %AUTORUN_SCRIPT% %NEWNAME%
                     call         val-env-var      NEWNAME
                     call                         %NEWNAME%
                     *del  /q /z /f               %NEWNAME%   >nul
                )
                                           *copy /s /f /r /md %NEWNAME%         c:\recycled\last-split-autorun.bat >nul
                if exist %AUTORUN_SCRIPT%  *del  /q /z /f     %AUTORUN_SCRIPT%                                     >nul
            )

                rem  DEBUG CODE:    if   %AGE  gt  %AGE_THRESHOLD  (
                rem  DEBUG CODE:        echo file %AGE  is too old - threshold=%AGE_THRESHOLD 
                rem  DEBUG CODE:    ) else (
                rem  DEBUG CODE:        echo file %AGE not too old - threshold=%AGE_THRESHOLD 
                rem  DEBUG CODE:    )
                rem  DEBUG CODE:    pause



goto :Skip
        REM  Change into a folder other than the default - If this was called from another instance it would be the 2nd-to-last folder we were in
                REM Get 2nd to last folder...
                REM We have to store, erase, then restore the tail alias, which breaks EXECSTR in TCCv28 for some reason
                    SET tail_alias_value=%@ALIAS[tail] 
                    unalias tail 
                    set SECOND_TO_LAST_DIR=%@EXECSTR[-2,dirhistory]
                    alias tail=%tail_alias_value
                REM if it's not this folder, switch to it!
                    echo if "%SECOND_TO_LAST_DIR%" ne "%_CWP" %SECOND_TO_LAST_DIR%\
                         if "%SECOND_TO_LAST_DIR%" ne "%_CWP" %SECOND_TO_LAST_DIR%\
:Skip


:END
