@loadbtm on
@Echo Off
@on break cancel

rem Capture parameters:
        set pl=%1

rem Validate environment (once):
        iff "1" !=  "%validated_convert_pl_2_ones_missing_karaoke_but_with_lyrics%" then
                call validate-in-path check_playlist_for_files_without_txt_or_transcription.py create-srt-from-file.bat get-lyrics-for-file.btm get-karaoke get-lyrics
                set  validated_convert_pl_2_ones_missing_karaoke_but_with_lyrics=1
        endiff
        
rem When called with no parameters:
        iff "%1" == "" then
                call error "Must supply a playlist as argument"
                goto /i END
        endiff

rem Validate parameter existence:
        if not exist %pl% call validate-environment-variable pl

rem Validate parameter extension:
        set ext=%@EXT["%pl%"]
        if  "%EXT%" != "m3u" call fatal_error "Must pass a playlist to “%0”, not a file of another extension such as “%extT”"

rem Do the actual work:
        set NEW_PLAYLIST_NAME=%@FULL[%@UNQUOTE[%@NAME["%@UNQUOTE["%PL%"]"]]-without txt or lrc or srt.m3u]
echo        check_playlist_for_files_without_txt_or_transcription.py %pl% "%NEW_PLAYLIST_NAME%"
pause
        check_playlist_for_files_without_txt_or_transcription.py %pl% "%NEW_PLAYLIST_NAME%"


rem Validate the existence of the output file:
        if not exist "%NEW_PLAYLIST_NAME%" call validate-environment-variable NEW_PLAYLIST_NAME


:END
