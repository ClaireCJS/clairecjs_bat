@Echo Off
@on break cancel


::::: VALIDATE ENVIRONMENT:
        if 1 ne %VALIDATED_RENUMBER_ALL_MUSIC_FILES_FOR_RANDOMOSITY  (
            set  VALIDATED_RENUMBER_ALL_MUSIC_FILES_FOR_RANDOMOSITY=1
            call validate-in-path  warning advice success less_important divider rn
            call validate-env-vars temp filemask_audio
        )


::::: CONFIGURE TEMP FILE LOCATION / NAME —— Do not use a filename with spaces in it
        set OLD_NAMES_BACKUP=%temp\undo-RENUMBER-%_PID.txt                                    
 

::::: WARN:
        if "%1" eq "fast" (goto :fast_1)
        cls
        echo.
        call warning        "THIS WILL RENUMBER ALL MUSIC FILES IN THE CURRENT FOLDER"
        echo.
        call warning        "There is no going back"
        echo.
        call advice         "Old filenames will be saved in “%OLD_NAMES_BACKUP%”"
        pause


::::: PREVIEW:
    cls
    echo.
    call less_important "first, a sample of what it will do:"
    echo.
    pause
    color bright yellow on black
    rem COPY NERF’ED DO_IT SECTION FROM BELOW TO HERE:
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
    :fast_1
    echo.
    call divider
    echo.
    echo.


::::: SAVE UNDO INFORMATION:
    dir /bs/a: >%OLD_NAMES_BACKUP%


::::: DO IT!
    set NUM_FILES=%@FILES[%filemask_audio%]
    set CUR_FILE=%NUM_FILES
    rem RN_DECORATOR=%EMOJI_INPUT_NUMBERS%
    set DECORATOR=%EMOJI_GAME_DIE%
    for /a:-d /h %audiofile in (%filemask_audio%) ( set rand=%@FORMAT[04,%@RANDOM[0,9999]] %+ echos %STAR% %cur_file% %faint_on%left: %faint_off%%DECORATOR%%@RANDFG[]%rand%%DECORATOR% %EMOJI_RIGHT_ARROW% %+ call rn "%audiofile" "%rand%_%@REREPLACE[[0-9]*[\-_]+ *,,%audiofile]" fast %+ set CUR_FILE=%@EVAL[%cur_file - 1] )
    unset /q RN_DECORATOR

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

