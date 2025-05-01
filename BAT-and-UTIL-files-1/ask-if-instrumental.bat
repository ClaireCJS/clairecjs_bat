@loadbtm on
@Echo OFF



rem Validate environment (once):
        iff "1" != "%validated_askifinstrumental%" then
                call validate-environment-variables italics_on italics_off star star2 ansi_color_warning_soft ansi_color_removal ansi_color_normal                                                 %+ rem trust me that the ones that aren’t directly referenced in this bat file are actually required too
                call validate-in-path ask-if-these-are-instrumentals.bat warning print-message
                set  validated_askifinstrumental=1
        endiff

rem Store original %ANSWER%:
        if defined answer set hold_answer_aif=%answer%


rem Main:
        iff "%@UNQUOTE["%1"]" == "" then
                call ask-if-these-are-instrumentals.bat  %*
        elseiff exist %1 then
                gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instrumental %1 instrumental ask
        else
                call warning "Not sure what to do..."
        endiff


rem Restore original %ANSWER%:
        iff defined hold_answer_aif then
                set answer=%hold_answer_aif%
                unset /q hold_answer_aif
        endiff