@Echo OFF                                       

call  validate-environment-variables BAT DROPBOX
set   SYNCSOURCE=%BAT%                         
set   SYNCTARGET=%DROPBOX%\BACKUPS\BAT\
set   SYNCTRIGER=__ last synced to dropbox __   
call  sync-a-folder-to-somewhere.bat ZIP /[!.git *.bak]            
            
