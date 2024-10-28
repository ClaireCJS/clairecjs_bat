@Echo OFF

rem Go to currently playing song's folder:
        call go-to-currently-playing-song-dir

rem Make sure the previous script currently set %CURRENT_SONG_FILE%
        call validate-environment-variable current_song_file
        set    CREATING_LRC_FOR_SONG_FILE=%CURRENT_SONG_FILE%

rem Create an LRC file for that file:
        call create-lrc-from-file "%CURRENT_SONG_FILE%" %*
