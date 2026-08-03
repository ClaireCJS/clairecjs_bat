@loadbtm on
@Echo Off
@on break cancel

rem Validate environment (once):
        iff "1" != "%validated_create_srt_file_for_currently_playing_song%" then
                call validate-in-path go-to-currently-playing-song-dir errorlevel fatal_error WhisperTimeSync
                call validate-environment-variables ansi_colors_have_been_set
                set  validated_create_srt_file_for_currently_playing_song=1
        endiff


rem Capture parameters we will use later:
        set PARAM_ONE=%@UNQUOTE[%1]


rem GO to the currently playing song folder to process
        call go-to-currently-playing-song-dir
        call errorlevel

rem Make sure the previous script currently set %CURRENT_SONG_FILE%
        if not defined current_song_file call fatal_error "'%italics_on%current_song_file%italics_off%' is not defined in %0 and should be"
        set WTCCAF_SRT=%@NAME[%@UNQUOTE["%CURRENT_SONG_FILE%"]].srt
        set WTCCAF_TXT=%@NAME[%@UNQUOTE["%CURRENT_SONG_FILE%"]].txt
        if not exist "%WTCCAF_SRT%" call validate-environment-variable WTCCAF_SRT "No subtitle%zzzz% file for audio file: %italics_on%%CURRENT_SONG_FILE%%italics_off%"
        if not exist "%WTCCAF_TXT%" call validate-environment-variable WTCCAF_TXT "No lyric%zzzzzzz% file for audio file: %italics_on%%CURRENT_SONG_FILE%%italics_off%"

rem Create an LRC file for that file:
        echo %ansi_color_subtle%`>`call WhisperTimeSync %* "%WTCCAF_SRT%" "%WTCCAF_TXT%" "%CURRENT_SONG_FILE%" %ansi_color_normal
                                   call WhisperTimeSync %* "%WTCCAF_SRT%" "%WTCCAF_TXT%" "%CURRENT_SONG_FILE%" 
                   set LATSCOMMAND=call WhisperTimeSync %* "%WTCCAF_SRT%" "%WTCCAF_TXT%" "%CURRENT_SONG_FILE%" 

:END