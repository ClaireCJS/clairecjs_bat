@Echo OFF

if "%1" eq "" (%COLOR_ADVICE% %+ echo USAGE:   ensure-directories-exist _NEW TEMP TEMP1 X Y Z "MY FOLDER" "d:\a folder" %+ goto :END)

    for %d in (%*) do if not exist %d md %d

:END

