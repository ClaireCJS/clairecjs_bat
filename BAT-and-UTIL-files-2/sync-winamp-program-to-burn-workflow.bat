@Echo OFF                                       

set   SYNCSOURCE=%util2%\WinAmp repo\WinAmp
set   SYNCTARGET=%PREBURN_BDR_DATA%\BACKUPS
set   SYNCTRIGER=__ last backed up to bdr-burn workflow __
call  sync-a-folder-to-somewhere.bat zip


            
