@Echo Off
 on break cancel
 
rem Get parameters:
        set Lyric_File_To_Display_Status_Of=%@unquote[%1]                                               %+ rem Lyric file to use 
        set PARAM_2=%2

rem Validate environment:
        iff 1 ne %VALIDATE_LYRIC_APPROVE_DISAPPROVE% then
                call validate-in-path add-ads-tag-to-file
                call validate-environment-variables italics_on italics_off newline filemask_audio
                set  VALIDATE_LYRIC_APPROVE_DISAPPROVE=1
        endiff                
        
rem Validate parameters:
        call validate-environment-variable Lyric_File_To_Display_Status_Of  "1ˢᵗ arg to %italics_on%display-lyric-status%italics_off% must be a lyric file that exists and was “%lyric_file_to_display_status_of%”. 2ⁿᵈ optional arg can be “%italics_on%verbose%italics_off%”." %+ rem 3ʳᵈ  optional arg can be “%italics_on%lyriclessness%italics_off%”
        
        iff "%PARAM_2" eq "lyriclessness" then    %+ rem ...then we’re actually operating on a song file
                call validate-is-extension "%Lyric_File_To_Display_Status_Of%" %FILEMASK_AUDIO% "Extension of the audio file must be one of “%FILEMASK_AUDIO%”%newline%[cmdline was “%0 %@unquote[%*]”]"
                set  tag=lyriclessness
        else                
                call validate-is-extension "%Lyric_File_To_Display_Status_Of%" *.txt            "Extension of the lyric file must be “.txt”%newline%%zzzzzzzzzzzzzzzzz%[cmdline was “%0 %@unquote[%*]”]"
                set  tag=lyrics
        endiff                

rem Set via windows alternate data streams:
        call read-ads-tag-from-file "%Lyric_File_To_Display_Status_Of%" %tag% lyrics %+ rem sets RECEIVED_VALUE for return value (one parameter is specificying the lyrics tag, the other is specifying that we run in lyrics mode with custom lyric-specific output)
        rem echo received_value=“%received_value%”
