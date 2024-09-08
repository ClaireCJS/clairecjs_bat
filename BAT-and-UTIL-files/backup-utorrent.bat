@Echo OFF

::::: ENVIRONMENT VALIDATION:
    call validate-environment-variables TEMP MACHINENAME

::::: UPDATE USER:
    call important "Running uTorrent backup"

::::: DETERMINE SOURCE TO ZIP:
    set FOLDER_TO_ZIP=%APPDATA%\uTorrent                 
    if isdir "%FOLDER_TO_ZIP%" goto :Exists
        :Folder_Does_Not_Exist
            call fatal_error "uTorrent not present at %FOLDER_TO_ZIP%"
        goto :END
    :Exists

::::: DETERMINE TARGET ZIPFILE:
    call yyyymmdd
    set TARGET=%TEMP\uTorrent-%MACHINENAME%-settings-%YYYYMMDD.zip

::::: CREATE THE ZIP:
    set USE_ZIP_NAME="%TARGET"
    call zip-folder "%FOLDER_TO_ZIP%"                  
    
::::: VERIFY CREATION:
    call validate-environment-variable TARGET

::::: BACKUP THE FILE WE CREATED:
    (echo yryryryryryr|call backup-to-every-drive "%TARGET%")
    

:END

