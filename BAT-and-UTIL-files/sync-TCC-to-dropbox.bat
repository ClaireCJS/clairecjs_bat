@Echo oFF
call validate-environment-variable DROPBOX
set SYNCSOURCE=c:\TCMD
set SYNCTARGET=%DROPBOX%\BACKUPS\TCMD
set SYNCTRIGER=__ last backed up to dropbox zipfile __
call sync-a-folder-to-somewhere.bat ZIP

