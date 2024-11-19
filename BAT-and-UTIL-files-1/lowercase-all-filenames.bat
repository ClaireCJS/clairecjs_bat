@on break cancel
@Echo OFF


::::: VALIDATE ENVIRONMENT:
        if 1 ne %VALIDATED_LOWERCASED_FILENAMES  (
            set  VALIDATED_LOWERCASED_FILENAMES=1
            call validate-in-path  warning advice success less_important divider 
            call validate-env-vars temp 
        )


::::: CONFIGURE TEMP FILE LOCATION / NAME —— Do not use a filename with spaces in it
        set SUCCESS_MESSAGE=Filenames lowercased!
        set DIRECTORY_BACKUP=%temp\undo-LOWERCASING-of-filenames-%_PID-%_DATETIME.txt                                    
 

::::: WARN:
        cls
        echo.
        call warning        "THIS WILL LOWERCASE ALL FILENAMES!"
        echo.
        call warning        "There is no going back... You lose that capitalization information forever"
        echo.
        call advice         "Original filenames will be saved in '%DIRECTORY_BACKUP%'"
        pause


::::: PREVIEW:
    cls
    echo.
    call less_important "first, a sample of what it will do:"
    echo.
    color bright yellow on black
    for %file in (*) do echo ren "%file" "%@LOWER[%file]"
    echo.
    pause

    echo.
    echo.
    echo.
    call warning "If that is okay, then press any key %blink_on%[5X]%blink_off% to proceed with actually doing it"

    pause
    pause
    pause
    pause
    pause
    echo.
    call divider
    echo.
    echo.


::::: SAVE UNDO INFORMATION:
    dir /bs/a: >%DIRECTORY_BACKUP%


::::: DO IT! —— COLLAPSE ALL THE FOLDERS!:
    for %file in (*) do (echos %@RANDFG[] %+ ren "%file" "%@LOWER[%file]")


::::: SHOW SUCCESS:
    echo.
    call divider
    echo.

    call success "%SUCCESS_MESSAGE%"

    echo.
    call divider
    echo.

    %color_success%
    dir

