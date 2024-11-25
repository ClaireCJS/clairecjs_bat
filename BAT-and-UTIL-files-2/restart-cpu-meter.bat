@Echo OFF
@on break cancel

call removal "Killing tray CPU-meter"
        call killIfRunning taskmgr taskmgr 

rem call warning "Waiting 3 seconds..."
        call wait 3 "(waiting 3 seconds)"

call less_important "Re-starting tray CPU-meter..."
        start "" /min taskmgr



