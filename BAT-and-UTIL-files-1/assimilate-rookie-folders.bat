@Echo Off

set ASSIMILATION_TARGET=%GAMES%\VR\Rookie PSVR

call validate-environment-variables GAMES ASSIMILATION_TARGET

echo.
for /a:d /h %1 in (*.*) do gosub process_folder_1 "%1"

goto :END


    :process_folder_1 [tmp_folder]
        rem Skip certain exceptions...
                if %tmp_folder% eq "!!! THIS IS ROOKIE PCVR, NOT ROOKIE SIDELOADER !!!" (return)
                if %tmp_folder% eq "DONE"                                               (return)
                call important_less "Processing folder '%@UNQUOTE[%tmp_folder%]'..."

        rem Move into folder....
                pushd .
                set ASSIMILATE_COMMAND=*move  /g /z /a: /ds /MD %tmp_folder% "%ASSIMILATION_TARGET%\%@UNQUOTE[%tmp_folder%]"
                echo                %ASSIMILATE_COMMAND%f
                %COLOR_REMOVAL%
                echo y | %ASSIMILATE_COMMAND%
                %COLOR_NORMAL%
    return


:END

echo.
call advice "If we are done moving, we could always run backup-games to backup the work"

