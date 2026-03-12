@Echo OFF
@on break cancel


rem Kill CPU meter:
        call removal "Killing tray CPU-meter"
        rem call killIfRunning taskmgr taskmgr 
        kill /f procexp* >&>nul
        call wait 3 "(waiting 3 seconds)"

rem Restart CPU meter:
        call less_important "Re-starting tray CPU-meter, then minimizing it..."
        start "" /min taskmgr

rem Minimize CPU meter:       
        call wait 4 "(waiting 4 seconds)"
        call minimize "Process Explorer*"



