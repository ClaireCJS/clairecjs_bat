@Echo off

rem In XP, the tray-cpu meter that comes with taskmgr goes away unless you also restart taskman, so this will save us having to close it and reopen it:
        if "%OS"=="XP" (call less_important "Killing task manager..." %+ kill /f taskmgr )
        if "%OS"!="XP" (call less_important "Killing procexp..."      %+ kill /f procexp )


call less_important "Killing explorer..."
        kill /f explorer

call less_important "Wait 3 seconds..."
        call sleep 3

call less_important "Starting explorer..."
        start explorer

:restart the cpu meter in our tray:
        call restart-cpu-meter


