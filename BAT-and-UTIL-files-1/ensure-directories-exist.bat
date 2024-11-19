@on break cancel
@Echo OFF

rem Make sure we called this right:
        if "%1" eq "" (
            %COLOR_ADVICE% 
            echo USAGE:   ensure-directories-exist _NEW TEMP TEMP1 X Y Z "MY FOLDER" "d:\a folder" 
            goto :END
        )


rem If we did, do the work and ensure the directory exists:
        for %d in (%*) do if not exist %d md %d

:END

