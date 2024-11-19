@Echo Off
 on break cancel

rem Capture parameters we will use later:
        set PARAM_ONE=%@UNQUOTE[%1]


rem If we passed a filename, this isn't the script we actually wanted.
rem If we didn't, then go to the currently playing song folder to process
        iff exist "%PARAM_ONE%" then
                call warning "You actually meant to run %emphasis%create-lrc-from-file%deemphasis%%ansi_color_warning% ... Running that next."
                call pause-for-x-seconds 120
                rem Transfer control to new script (so don't use `call`):
                create-lrc-from-file %* 
                goto :END
        else
                call go-to-currently-playing-song-dir
                call errorlevel
        endiff

rem Make sure the previous script currently set %CURRENT_SONG_FILE%
        call validate-environment-variable current_song_file
        set    CREATING_LRC_FOR_SONG_FILE=%CURRENT_SONG_FILE%

rem Create an LRC file for that file:
        call create-lrc-from-file "%CURRENT_SONG_FILE%" %*

:END