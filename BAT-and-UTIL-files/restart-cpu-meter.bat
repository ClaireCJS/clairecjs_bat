@Echo OFF

%color_removal% %+ echo. %+ @Echo * Killing tray CPU-meter
    %color_run% %+ call killIfRunning taskmgr taskmgr 

%color_warning% %+ echo. %+ @Echo * Waiting 3 seconds...
    %color_run% %+ call sleep 3

%color_success% %+ @Echo * Re-starting tray CPU-meter...
    %color_run% %+ start /min taskmgr

