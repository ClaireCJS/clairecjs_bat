@loadbtm on
@Echo off

rem backup Xenia emulator savegames into monthly folders

::::: VALIDATE ENVIRONMENT:
        iff 1 ne %validated_bccjspyutil% then
                call validate-environment-variables PUBCL MACHINENAME python_claire_drive_backup
                call validate-in-path fast_cat
                set  validated_bccjspyutil=1
        endiff                
    
:::: SET UP SYNC:
    set SYNCSOURCE=%PUBCL%\Dev\py\clairecjs_utils
    set SYNCBASE=%python_claire_drive_backup%:\backups\clairecjs_utils\

    if not isdir %SYNCBASE% (md /s %SYNCBASE%)
    call yyyymmdd
    set SYNCTARGET=%SYNCBASE%\%YYYY%%MM%-%MACHINENAME%
    if not isdir %SYNCTARGET% (md /s %SYNCTARGET%)

    set SYNCTRIGER=__ last backed up __   


::::: PERFORM SYNC:
    call validate-environment-variables SYNCSOURCE SYNCTARGET
    (call sync-a-folder-to-somewhere.bat) |:u8 fast_cat
    rem *copy /e /w /u /s /r /a: /h /z /k /g /Nt "%@UNQUOTE[%SYNCSOURCE%]" "%@UNQUOTE[%SYNCTARGET%]" |:u8 copy-move-post

rem ::::: DELETE TRIGGER FILE, I DON'T LIKE SEEING IT:
rem      set DELETE=%SYNCTARGET%\%SYNCTRIGER%                        
rem      if exist  "%DELETE%" (%COLOR_REMOVAL% %+ *del "%DELETE%" %+ %COLOR_NORMAL%)

