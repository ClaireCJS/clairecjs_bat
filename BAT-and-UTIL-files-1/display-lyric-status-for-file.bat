@Echo OFF
 on break cancel
 
rem Get parameters:
        set LYRIC_FILE_TO_DISPLAY_STATUS_OF=%1                                                      %+ rem Lyric file to use 

rem Validate environment and parameter:
        iff 1 ne %VALIDATE_LYRIC_APPROVE_DISAPPROVE% then
                call validate-environment-variable LYRIC_FILE_TO_DISPLAY_STATUS_OF "1ˢᵗ arg must be a lyric file. 2ⁿᵈ can be '%italics_on%verbose%italics_off%'"
                call validate-is-extension         LYRIC_FILE_TO_DISPLAY_STATUS_OF *.txt
                call validate-in-path              add-ads-tag-to-file
                set  VALIDATE_LYRIC_APPROVE_DISAPPROVE=1
        endiff                

rem Set via windows alternate data streams:
        iff 0 ne %LYRIC_JUSTIFICATION% then
                call read-ads-tag-from-file %LYRIC_FILE_TO_DISPLAY_STATUS_OF% lyrics lyrics %+ rem sets RECEIVED_VALUE for return value (one parameter is specificying the lyrics tag, the other is specifying that we run in lyrics mode with custom lyric-specific output)
                rem echo received_value='%received_value%'
        else
                call read-ads-tag-from-file %LYRIC_FILE_TO_DISPLAY_STATUS_OF% lyrics lyrics 
        endiff
