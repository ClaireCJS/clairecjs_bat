@Echo OFF
@on break cancel
 title %_CWP


rem set NOPAUSE=1 when automating this through folder trees——calls to 'divider.bat' slow things down so some of that is prevented too

::::: VALIDATE ENVIRONMENT:
        if 1 ne %VALIDATED_PERCENT_REMOVAL_FROM_FILENAMES (
            set  VALIDATED_XBOX360_FILENAME_FIXER=1
            call validate-in-path  warning advice success less_important divider 
            call validate-env-vars temp 
        )


::::: CONFIGURE TEMP FILE LOCATION / NAME —— Do not use a filename with spaces in it
        set DIRECTORY_TREE_BACKUP=%temp\undo-remove-percents-from-filenames-%_PID.txt                                    
 

::::: WARN:
        cls
        if %NOPAUSE eq 1 (goto :NoPause_1)
        echo.
        call warning        "THIS WILL REMOVE ALL PERCENT-SIGNS FROM FILENAMES!"
        echo.
        call warning        "There is no going back... You lose a lot of the filenames"
        echo.
        call advice         "Directory tree will be saved in '%DIRECTORY_TREE_BACKUP%'"
        pause
        :NoPause_1

::::: PREVIEW:
    cls
    echo.
    call less_important "first, a sample of what it will do:"
    title %_CWP
    echo.
    color bright yellow on black
    setdos /x-4
    for /h %filename in ("*%*") do ( %+ echo ren "%filename" "%@REPLACE[%%,,%filename]"  )
    setdos /x-0
    echo.
    pause

    if %NOPAUSE ne 1 (
        echo.
        echo.
        echo.
        call warning "If that is okay, then press any key %blink_on%[5X]%blink_off% to proceed with actually doing it"
        title %_CWP
        pause
        pause
        pause
        pause
        pause
        echo.
        call divider
    )

    echo.
    echo.


::::: SAVE UNDO INFORMATION:
    dir /bs/a: >%DIRECTORY_TREE_BACKUP%


::::: DO IT!:
    setdos /x-4
    for /h %filename in ("*%*") do ( ren "%filename" "%@REPLACE[%%,,%filename]"  )
    setdos /x-0


::::: SHOW SUCCESS:
    if %NOPAUSE ne 1 (
        echo.
        call divider
    )

    echo.
    call success "Filenames fixed!"

    if %NOPAUSE ne 1 (
        echo.
        call divider
        echo.

        %color_success%
        dir
    )

color bright cyan on black
