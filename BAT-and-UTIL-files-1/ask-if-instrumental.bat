@loadbtm on
@Echo OFF



rem Validate environment (once):
        iff "Y" != "%validated_askifinstrumental%" then
                call validate-environment-variables ansi_colors_have_been_set emojis_have_been_set 
                call validate-in-path ask-if-these-are-instrumentals.bat warning print-message unmark-all-filenames-ADS-tag-for-as_instrumental.bat warning success advice
                set  validated_askifinstrumental=Y
        endiff

rem Store original %ANSWER%:
        if defined answer set hold_answer_aif=%answer%

rem Flush previous “No” answers that were stored in files’ ADS tags:
        if "%1" == "force" call unmark-all-filenames-ADS-tag-for-as_instrumental.bat

rem Main:
        @set SOME_INSTRUMENTALS_WERE_MARKED=0
        unset already_asked_about*
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


rem Did we rename any?
        iff "1" == "%SOME_INSTRUMENTALS_WERE_MARKED%" then
                call success "Some instrumentals were marked!"
        else
                echo.                                
                call warning "No files were renamed/marked"
                call advice  "Try the “force” option if it didn’t ask you about files previously-marked as “False” for instrumental"
        endiff
