@Echo oFF



call validate-in-path check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py



iff "%1" == "" then
        echo Must supply playlist as argument
        goto :END
endiff

set pl=%1

if not exist %pl% call validate-environment-variable pl

set ext=%@EXT["%pl%"]
if  "%EXT%" != "m3u" call fatal_error "Gotta pass a playlist to %0, not a file of another extension such as “%extT”"

check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py %pl *.lrc;*.srt 

set NEW_PLAYLIST_NAME=%@UNQUOTE[%@NAME["%@UNQUOTE["%PL%"]"]]-without lrc or srt.m3u
call validate-environment-variable NEW_PLAYLIST_NAME


:END
