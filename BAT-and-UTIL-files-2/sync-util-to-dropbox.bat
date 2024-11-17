@Echo on

call validate-environment-variables UTIL DROPBOX

set SYNCSOURCE=%UTIL%
set SYNCTARGET=%DROPBOX%\BACKUPS\UTIL\
set SYNCTRIGER=__ last backed up to dropbox zipfile __
call sync-a-folder-to-somewhere.bat /[!.git *.bak]            

