@on break cancel
@Echo OFF


::::: VALIDATE ENVIRONMENT:
        if 1 ne %VALIDATED_DRASTICALLY_SHORTEN_AND_STANDARDIZE_FILENAMES  (
            set  VALIDATED_DRASTICALLY_SHORTEN_AND_STANDARDIZE_FILENAMES=1
            call validate-in-path  warning advice success less_important divider 
            call validate-env-vars temp 
        )


::::: CONFIGURE TEMP FILE LOCATION / NAME —— Do not use a filename with spaces in it
        set DIRECTORY_TREE_BACKUP=%temp\undo-drastically-shorten-and-standardize-filenames-%_PID.txt                                    
 

::::: WARN:
        cls
        echo.
        call warning        "THIS WILL SHORTEN ALL FILENAMES TO 32-ISH CHARS AND ELIMINATE ALL SPACES"
        echo.
        call warning        "There is no going back... You lose a lot of the filenames"
        echo.
        call advice         "Directory tree will be saved in “%DIRECTORY_TREE_BACKUP%”"
        pause


::::: PREVIEW:
    cls
    echo.
    call less_important "first, a sample of what it will do:"
    echo.
    color bright yellow on black
    for /h %filename in (*.*) do if %@LEN[%filename] gt 32 (echo ren "%filename" "%@REPLACE[(,_,%@REPLACE[ ,_,%@LEFT[24,%filename]%@RIGHT[1,%_DATETIME]%@RANDOM[1,999].%@EXT[%filename]]]") 
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
    dir /bs/a: >%DIRECTORY_TREE_BACKUP%


::::: DO IT! —— COLLAPSE ALL THE FOLDERS!:
    for /h %filename in (*.*) do if %@LEN[%filename] gt 32 (    *ren "%filename" "%@REPLACE[,,,%@REPLACE[(,_,%@REPLACE[ ,_,%@LEFT[24,%filename]%@RIGHT[1,%_DATETIME]%@RANDOM[1,999].%@EXT[%filename]]]]") 


::::: SHOW SUCCESS:
    echo.
    call divider
    echo.

    call success "Folders collapsed!"

    echo.
    call divider
    echo.

    %color_success%
    dir

