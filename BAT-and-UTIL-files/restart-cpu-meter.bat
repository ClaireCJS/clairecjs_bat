@Echo OFF

call removal ""Killing tray CPU-meter"
        call killIfRunning taskmgr taskmgr 

call warning "Waiting 3 seconds..."
        call wait 3

call less_important "Re-starting tray CPU-meter..."
        start /min taskmgr



