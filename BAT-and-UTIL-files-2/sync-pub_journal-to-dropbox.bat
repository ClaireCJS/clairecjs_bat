@Echo OFF                                       


rem   Backup my c:\pub\journal\ folder to dropbox

rem   Good example of sync-a-folder-to-somewhere invocation-by-environment_variable


call  validate-environment-variableS PUBCL DROPBOX
set   SYNCSOURCE=%PUBCL%\journal
set   SYNCTARGET=%DROPBOX%\BACKUPS\PUB\JOURNAL
set   SYNCTRIGER=__ last synced to dropbox __   
call  sync-a-folder-to-somewhere.bat /[!.git *.bak]            
            
