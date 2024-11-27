@Echo OFF

set DIRT=AI transcription trash files

call important_less "You must decide whether to do it here, or everywhere:"

        call AskYN "Clean up %DIRT% %italics_on%%blink_on%here%blink_off%%italics_off%?"
                
                iff "%ANSWER%" == "Y" then
                        call divider
                        call clean-up-AI-transcription-trash-files-here
                        call errorlevel "problem in trash-cleaning script clean-up-AI-transcription-trash-files-here"
                        call divider
                endiff
                
        call AskYN "Clean up %DIRT% %italics_on%%blink_on%everyhere%blink_off%%italics_off%?"

                iff "%ANSWER%" == "Y" then
                        call clean-up-AI-transcription-trash-files-everywhere
                        call errorlevel "problem in trash-cleaning script clean-up-AI-transcription-trash-files-everywhere"
                        call divider
                endiff

call success "All clean!"

