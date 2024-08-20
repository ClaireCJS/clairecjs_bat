@Echo OFF                                       

call  validate-environment-variableS PUBCL DROPBOX
set   SYNCSOURCE=%PUBCL%\journal
set   SYNCTARGET=%DROPBOX%\BACKUPS\PUB\JOURNAL
set   SYNCTRIGER=__ last synced to dropbox __   
call  sync-a-folder-to-somewhere.bat /[!.git *.bak]            
            
