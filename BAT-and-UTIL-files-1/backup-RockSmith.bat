@loadbtm on
@Echo OFF                                       
 on break cancel

::::: SET ENV VAR FOR BACKUP:
    set RSBACKUPS=%GAMESBACKUP%\RHYTHM & MUSIC\ROCKSMITH

::::: VALIDATE ENVIRONMENT:
    call validate-environment-variables GAMES RSBACKUPS GAMESBACKUP

:::: SET UP SYNC:
    set SYNCSOURCE="%games%\RHYTHM & MUSIC\RockSmith\"
    set SYNCTARGET=%RSBACKUPS%              
    set SYNCTRIGER=__ last backed up __   

::::: PERFORM SYNC:
    call sync-a-folder-to-somewhere.bat

rem ::::: DELETE TRIGGER FILE, I DON'T LIKE SEEING IT:
rem      set DELETE=%DELETEAFTERWATCHING%\%SYNCTRIGER%                        
rem      if exist  "%DELETE%" (%COLOR_REMOVAL% %+ *del "%DELETE%" %+ %COLOR_NORMAL%)

