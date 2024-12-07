@Echo off
 on break cancel
 set PARAMS=%*

rem Get parameters:
        set LYRIC_FILE_TO_APPROVE=%@UNQUOTE[%1]                                              %+ rem Lyric file to use 

rem Validate environment once:
        iff 1 ne %VALIDATE_LYRIC_APPROVE_DISAPPROVE% then
                call validate-in-path add-ads-tag-to-file
                set  VALIDATE_LYRIC_APPROVE_DISAPPROVE=1
        endiff                

rem Validate parameters every time:
        call validate-environment-variable   Lyric_File_To_Approve   "1ˢᵗ arg must be a lyric/subtitle file. 2ⁿᵈ optional arg can be a tag other than 'lyrics' to add to file, 3ʳᵈ can be a value other than approved/not_approved/etc to add to file"
        call validate-is-extension         "%Lyric_File_To_Approve%" *.txt;*.srt;*.lrc            %+ rem We will also sneak subtitles in, in case we decide to add approval for those down the road
        
rem Set via windows alternate data streams:
        call add-ads-tag-to-file "%LYRIC_FILE_TO_APPROVE%" lyrics APPROVED lyrics


