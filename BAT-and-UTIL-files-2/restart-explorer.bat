@Echo off

rem Validate environment:
        call validate-in-path removal kill wait start restart-cpu-meter
        call validate-environment-variables OS 

rem In XP, the tray-cpu meter that comes with taskmgr goes away unless you also restart taskman, so this will save us having to close it and reopen it:
        if "%OS"=="XP" (call removal "Killing task manager..." %+ kill /f taskmgr )
        if "%OS"!="XP" (call removal "Killing procexp..."      %+ kill /f procexp )


rem call less_important "Killing explorer..."
call     removal        "Killing explorer..."
        kill /f explorer

rem call less_important "Wait 3 seconds..."
        call wait 3 "(waiting 3 seconds)"

call less_important "Starting explorer..."
        start explorer

:restart the cpu meter in our tray:
        call restart-cpu-meter


