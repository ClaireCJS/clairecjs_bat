@Echo off

if not exist *.wav (call warning "No wavs to normalize! Aborting!" %+ goto :end)


:determine the filename of our report - which includes the date so as not to collide over the same file when moving things to a folder that already has one
    call yyyymmdd.bat
    SET REPORTFILENAME=normalization-report-%YYYYMMDD%.txt

:head the file with today's date and time:
    call  display-date-and-time-nicely       >>%REPORTFILENAME%
    echo.                                    >>%REPORTFILENAME%

:show the original peak values before we touch it:
    echo   level        peak         gain    >>%REPORTFILENAME%
    normalize -n --fractions -v *.wav        >>%REPORTFILENAME%

:then show us how they are fixed:
    %COLOR_IMPORTANT% %+ echo * Normalizing...
    %COLOR_RUN%       %+ normalize --fractions -v *.wav |& grep -i -v done.*ETA.*batch.*done |& tee /a %REPORTFILENAME%

:then show us our new peak values after touching it:
    echo   level        peak         gain    >>%REPORTFILENAME%
    normalize -n --fractions -v *.wav        >>%REPORTFILENAME%

:and output to the screen:
    %COLOR_SUCESS% %+ type %REPORTFILENAME%
    goto :end





:end
