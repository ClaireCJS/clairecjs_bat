@Echo OFF
@loadbtm on
 on break cancel
 
rem Get parameters:
        set song_file_to_approve=%@UNQUOTE[%1]                                               %+ rem song file to use 
        set txt_sidecar=%@name["%song_file_to_approve%"].txt

rem Validate environment once:
        iff 1 ne %VALIDATE_SONG_APPROVE_APPROVE% then
                call validate-in-path              add-ads-tag-to-file validate-environment-variable validate-is-extension
                call validate-environment-variable filemask_audio skip_validation_existence
                set  VALIDATE_SONG_APPROVE_APPROVE=1
        endiff                
        
rem Validate parameters every time
        if not exist "%@UNQUOTE["%Song_File_To_Approve%"]" call validate-environment-variable Song_File_To_Approve "1ˢᵗ arg must be a song file. 2ⁿᵈ optional arg can be a tag other than “lyrics” to add to file, 3ʳᵈ can be a value other than “approved”/“not_approved”/etc to add to file"
        call validate-is-extension       "%Song_File_To_Approve%" %FILEMASK_AUDIO%           

rem Set via windows alternate data streams:
        call add-ads-tag-to-file         "%song_file_to_Approve%" lyriclessness APPROVED lyrics

rem special case for approve-lyriclessness.bat only: 
rem If a lyric file exists, nuke it, because we’ve determined this can’t have lyrics found:
        if exist "%txt_sidecar%" (echo ray | *del /q "%txt_sidecar%")
