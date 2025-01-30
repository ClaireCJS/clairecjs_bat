@Echo OFF
@on break cancel

rem Go to currently playing song's folder:
        call go-to-currently-playing-song-dir

rem Make sure the previous script currently set %CURRENT_SONG_FILE%
        call validate-environment-variable current_song_file
        set    CREATING_LRC_FOR_SONG_FILE=%CURRENT_SONG_FILE%

rem Rename that file:
        iff "%1" == "as_instrumental" then
                shift
                call rn as_instrumental "%CURRENT_SONG_FILE%" 
        else
                call rn "%CURRENT_SONG_FILE%" 
        endiff
