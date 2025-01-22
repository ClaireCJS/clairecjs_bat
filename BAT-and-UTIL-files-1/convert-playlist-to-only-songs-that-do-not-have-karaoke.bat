@Echo OFF
@loadbtm on
@on break cancel

rem Validate environment (once):
        iff "1" !=  "%validated_convert_pl_2_ones_missing_karaoke%" then
                call validate-in-path check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py create-srt-from-file.bat get-lyrics-for-file.btm get-karaoke get-lyrics
                set  validated_convert_pl_2_ones_missing_karaoke=1
        endiff
        
rem When called with no parameters:
        iff "%1" == "" then
                call error "Must supply a playlist as argument"
                goto :END
        endiff

rem Capture parameters:
        set pl=%1

rem Validate parameter existence:
        if not exist %pl% call validate-environment-variable pl

rem Validate parameter extension:
        set ext=%@EXT["%pl%"]
        if  "%EXT%" != "m3u" call fatal_error "Must pass a playlist to “%0”, not a file of another extension such as “%extT”"

rem Do the acutal work:
        check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py %pl *.lrc;*.srt 

rem Validate the existence of the output file:
        set NEW_PLAYLIST_NAME=%@UNQUOTE[%@NAME["%@UNQUOTE["%PL%"]"]]-without lrc or srt.m3u
        call validate-environment-variable NEW_PLAYLIST_NAME

rem Now that we have a playlist of songs that do not have karaoke, ask if we want to get lyrics or karaoke for it:
rem (Unless we are being called by work.bat, which is handling this):
        if "%@NAME[%_PBATCHNAME]" == "work" .or. "1" == "%CURRENTLY_WORKING_RIGHT_NOW%" goto :skip_questioning
        echo.
        :ask
        call AskYN "Create karaoke files —— or fetch lyrics —— from the new playlist" no 60 KL K:Create_karaoke_from_new_playlist,L:Get_lyrics_for_new_playlist
        iff "Y" == "%ANSWER%" then
                beep
                echo %ansi_color_error% Please choose “K” or “L”! %ansi_color_normal%
                goto :ask
        endiff
        iff "K" == "%ANSWER%" then
                call get-karaoke "%NEW_PLAYLIST_NAME%" 50
        elseiff "L" == "%ANSWER%" then
                call get-lyrics  "%NEW_PLAYLIST_NAME%"
        endiff
        :skip_questioning

:END
