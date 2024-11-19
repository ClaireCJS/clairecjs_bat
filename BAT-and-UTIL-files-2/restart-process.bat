@Echo OFF
@on break cancel

rem BREAK IF NOT CALLED CORECTLY:
        if "%1" eq "" (goto :Usage)

rem CONFIGURATION CONSTANTS:
        SET DEFAULT_WAIT_TIME_AFTER_KILL=2
        SET DEFAULT_WAIT_TIME_AFTER_RESTART=4

rem VARIABLES BASED ON CONSTANTS:
        SET RESTART_WAIT_TIME_AFTER_KILL=%DEFAULT_WAIT_TIME_AFTER_KILL%
        SET RESTART_WAIT_TIME_AFTER_RESTART=%DEFAULT_WAIT_TIME_AFTER_RESTART%

rem PROCESS COMMAND-LINE ARGUMENTS FOR DIFFERENT INVOCATIONS:
        SET RESTART_NAME_PROCESS=%1
        SET RESTART_NAME_COLLOQIAL=%1
        SET RESTART_START_COMMAND=%1

        if "%2" ne "" (set RESTART_NAME_COLLOQIAL=%2)
        if "%3" ne "" (set RESTART_WAIT_TIME_AFTER_KILL=%3)
        if "%4" ne "" (set RESTART_WAIT_TIME_AFTER_RESTART=%4)
        if "%5" ne "" (set RESTART_START_COMMAND=%5)

rem PERFORM THE RESTART:
        call removal "Killing %RESTART_NAME_COLLOQIAL%..."
        call killIfRunning %RESTART_NAME_PROCESS% %RESTART_NAME_PROCESS%
        call wait %RESTART_WAIT_TIME_AFTER_KILL%
        call less_important Restarting %RESTART_NAME_COLLOQIAL%...
        %COLOR_RUN% 
        %RESTART_START_COMMAND%
        call  wait   %RESTART_WAIT_TIME_AFTER_RESTART%

rem EXPERRIMENTAL: ACTIVATE/BRING NEW WINDOW TO FRONT:
        rem echo Experiment: option to do "window restore [windowname]"  - may need a %RESTART_WINDOW_RESTORE_WINDOW_NAME%R option
        rem :example: window restore evilly~1


goto :END



            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            :Usage
                %COLOR_ADVICE%
                    echo USAGE #1: %0 chrome ————————————————————————— restarts the process named chrome using default settings (don't use quotes unless there is a space in it)
                    echo USAGE #2: %0 chrome webbrowser —————————————— same as #1 but says "restarting webbrowser" instead of "restarting chrome"
                    echo USAGE #3: %0 chrome webbrowser 4 ———————————— same as #3 but waits 4 seconds after the kill instead of the default of %DEFAULT_WAIT_TIME_AFTER_KILL% seconds
                    echo USAGE #4: %0 chrome webbrowser 4 6 —————————— same as #3 but waits 6 seconds after the kill instead of the default of %DEFAULT_WAIT_TIME_AFTER_RESTART% seconds
                    echo USAGE #5: %0 chrome webbrowser 4 6 firefox —— same as #4 but with a custom restart command (i.e. if you need command-line options, etc), in this case would kill chrome and start firefox.  
                    echo                                  The restart command may need to be "start /min [something]" for example
                    echo                                  %ANSI_COLOR_WARNING%May need to use %%@SFN[something] to get a spaceless filename.%ANSI_COLOR_advice%
                    echo.
                goto :END
            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:END
        :Cleanup_START
                rem CHANGE COLOR BACK TO NORMAL:    
                        %COLOR_NORMAL% 
                        echos %CURSOR_RESET%

                rem SAVE VALUES FOR AUDITING:
                        SET LAST_RESTART_NAME_PROCESS=%RESTART_NAME_PROCESS%
                        SET LAST_RESTART_NAME_COLLOQIAL=%RESTART_NAME_COLLOQIAL%
                        SET LAST_RESTART_WAIT_TIME_AFTER_KILL=%RESTART_WAIT_TIME_AFTER_KILL%
                        SET LAST_RESTART_START_COMMAND=%RESTART_START_COMMAND%

                rem CLEAR VARIABLES SO NO LEAKING TO SUCCESSIVE RUNS:
                        UNSET /q RESTART_NAME_PROCESS
                        UNSET /q RESTART_NAME_COLLOQIAL
                        UNSET /q RESTART_WAIT_TIME_AFTER_KILL
                        UNSET /q RESTART_START_COMMAND
        :Cleanup_END
:The_Very_End
