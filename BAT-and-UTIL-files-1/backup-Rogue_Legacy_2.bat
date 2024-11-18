@Echo OFF                                       

rem backup rogue legacy 2 savegame into monthly folders

::::: VALIDATE ENVIRONMENT:
    call validate-environment-variables AppData  MACHINENAME GAME_SAVES_BACKUPS
    
:::: SET UP SYNC:
    set SYNCSOURCE=%AppData%\..\LocalLow\Cellar Door Games\Rogue Legacy 2
    set SYNCBASE=%GAME_SAVES_BACKUPS%\Rogue_Legacy_2.%MACHINENAME%

    call validate-environment-variable SYNCBASE
    call yyyymmdd
    set SYNCTARGET=%SYNCBASE%\%YYYY%%MM%
    if not isdir %SYNCTARGET% (md /s %SYNCTARGET%)

    set SYNCTRIGER=__ last backed up __   


::::: PERFORM SYNC:
    call validate-environment-variables SYNCSOURCE SYNCTARGET
    call sync-a-folder-to-somewhere.bat 
    rem *copy /e /w /u /s /r /a: /h /z /k /g /Nt "%@UNQUOTE[%SYNCSOURCE%]" "%@UNQUOTE[%SYNCTARGET%]" |:u8 copy-move-post

rem ::::: DELETE TRIGGER FILE, I DON'T LIKE SEEING IT:
rem      set DELETE=%SYNCTARGET%\%SYNCTRIGER%                        
rem      if exist  "%DELETE%" (%COLOR_REMOVAL% %+ *del "%DELETE%" %+ %COLOR_NORMAL%)

