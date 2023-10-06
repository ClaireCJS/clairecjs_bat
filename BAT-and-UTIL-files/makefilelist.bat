@Echo off


    ::::: LET USER KNOW:
        color red   on black %+    echo * Making file list...
        color white on black

    ::::: DECIDE IF SLOW OR QUICK OR DIR:
        :quiet1
                         SET ATTRIBMASK=a-d %+ set TARGET_FILENAME=filelist.txt
        if "%1"=="/d"   (set ATTRIBMASK=ad  %+ set TARGET_FILENAME=dirlist.txt)
        if "%1"=="/q"   goto :quick
        if "%1"=="/s"   goto :slow
        if "%1"=="slow" goto :slow
        if "%1"=="size" goto :slow
        if "%1"=="full" goto :slow
        if "%1"=="/f"   goto :slow
                        goto :quick

    :quick
        :: the tricky part is that we need to exclude the name of the filelist itself from the produced list. Recursive playlists suck!
        dir /b /s  /[!%TARGET_FILENAME%] >%TARGET_FILENAME%
    goto :end

    :slow
    :full
        dir /b /s /a:%ATTRIBMASK% /[!%TARGET_FILENAME%] | sizedir %* | cut -c%@EVAL[%@LEN[%_CWDS] + 1]- >%TARGET_FILENAME%
    goto :end

:end
    set LAST_ATTRIBMASK=%ATTRIBMASK%
    unset /q ATTRIBMASK
    set LAST_TARGET_FILENAME=%TARGET_FILENAME%
    unset /q TARGET_FILENAME

