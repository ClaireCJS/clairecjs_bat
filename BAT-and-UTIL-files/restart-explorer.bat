@Echo off

rem In XP, the tray-cpu meter that comes with taskmgr goes away unless you also restart taskman, so this will save us having to close it and reopen it:
if "%OS"=="XP" (@Echo Killing task manager... %+ kill /f taskmgr )
if "%OS"!="XP" (@Echo Killing procexp...      %+ kill /f procexp )

@Echo Killing explorer...
kill /f explorer

@Echo Wait 3 seconds...
call sleep 3

@Echo Starting explorer...
start explorer

:restart the cpu meter in our tray:
call restart-cpu-meter
