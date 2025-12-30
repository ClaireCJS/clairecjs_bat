@loadbtm on
@Echo Off
 on break cancel

rem Validate environment (once):
        iff "1" != "%validated_fix_subtitles_file_for_currently_playing_song%" then
                call validate-in-path go-to-currently-playing-song-dir errorlevel validate-environment-variable subtitle-postprocessor.pl 
                set  validated_fix_subtitles_file_for_currently_playing_song=1
        endiff


rem Capture parameters we will use later:
        set PARAM_ONE=%@UNQUOTE[%1]


rem If we passed a filename, this isn't the script we actually wanted, we really wanted subtitle-processor.pl:
        iff exist "%PARAM_ONE%" then
                call subtitle-processor.pl %* 
                goto :END
                cancel
        else
                rem If we didn't, then go to the currently playing song folder to process
                call go-to-currently-playing-song-dir
                call errorlevel
        endiff

rem Make sure the previous script currently set %CURRENT_SONG_FILE%
        if not defined current_song_file call fatal_error "'%italics_on%current_song_file%italics_off%' is not defined in %0 and should be"
        set FIXING_SRT_FOR_SONG_FILE=%CURRENT_SONG_FILE%

rem Create an LRC file for that file:
        call subtitle-postprocessor.pl "%CURRENT_SONG_FILE%" %*

:END