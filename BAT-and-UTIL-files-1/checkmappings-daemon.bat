@loadbtm on
@Echo OFF
 on break cancel

rem Check the drive mappings:
        call checkmappings nopause

rem Wait an hour or however long:
        set WAIT_SECONDS=3600
        call wait %WAIT_SECONDS% "checking mappings every %@EVAL[%WAIT_SECONDS%/60] minutes"

rem Do it again!
rem (Execution transferred by not using 'call' on purpose in order to reload this BAT in case it has been changed)
        c:\bat\checkmappings-daemon.bat


