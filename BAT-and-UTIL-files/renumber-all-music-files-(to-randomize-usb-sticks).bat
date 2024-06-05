@Echo OFF


::::: VALIDATE ENVIRONMENT:
        if 1 ne %VALIDATED_RENUMBER_ALL_MUSIC_FILES_FOR_RANDOMOSITY  (
            set  VALIDATED_RENUMBER_ALL_MUSIC_FILES_FOR_RANDOMOSITY=1
            call validate-in-path  warning advice success less_important divider rn
            call validate-env-vars temp 
        )


::::: CONFIGURE TEMP FILE LOCATION / NAME —— Do not use a filename with spaces in it
        set OLD_NAMES_BACKUP=%temp\undo-RENUMBER-%_PID.txt                                    
 

::::: WARN:
        cls
        echo.
        call warning        "THIS WILL RENUMBER ALL MUSIC FILES IN THE CURRENT FOLDER"
        echo.
        call warning        "There is no going back"
        echo.
        call advice         "Old filenames will be saved in '%OLD_NAMES_BACKUP%'"
        pause


::::: PREVIEW:
    cls
    echo.
    call less_important "first, a sample of what it will do:"
    echo.
    pause
    color bright yellow on black
    for /a:-d /h %audiofile in (%filemask_audio%) ( echos %@RANDFG[] %+ echo rn "%audiofile" "%@FORMAT[04,%@RANDOM[0,9999]]_%@REREPLACE[[0-9]*[\-_]+ *,,%audiofile]" )
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
    dir /bs/a: >%OLD_NAMES_BACKUP%


::::: DO IT!
    for /a:-d /h %audiofile in (%filemask_audio%) ( echos %@RANDFG[] %+      rn "%audiofile" "%@FORMAT[04,%@RANDOM[0,9999]]_%@REREPLACE[[0-9]*[\-_]+ *,,%audiofile]" )


::::: SHOW SUCCESS:
    echo.
    call divider
    echo.

    call success "Audio files randomized!"

    echo.
    call divider
    echo.

    %color_success%
    rem dir

