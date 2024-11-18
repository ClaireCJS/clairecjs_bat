@Echo Off

set INSERT_TEXT=%1
if "%1" eq "SetVarsOnly" (goto :END)

call validate-environment-variable INSERT_TEXT

rem if exist "%inserttrigger%" (
rem     call warning "Already did this folder. Aborting. (inserttrigger file of %inserttrigger% exists)"
rem     goto :END
rem )

for /h %file in (*) do (gosub processfile "%@UNQUOTE[%file%]")
goto :Cleanup

            :processfile [FILE_QUOTED]
                set FILE_UNQUOTED=%@unquote[%file_quoted]
                *cls
                echo.
                echo %ANSI_COLOR_DEBUG%%STAR% Processing file %emphasis%%file_quoted%%deemphasis%...

                rem if "%@INSTR[0,%@LEN[%insert_text],%file_unquoted]" eq "%@UNQUOTE[%insert_text%]" 
                if %@REGEX[%insert_text,%file_unquoted] eq 1 (
                        echos      %ANSI_COLOR_WARNING%Skipping file '%file_unquoted%'...``%ANSI_COLOR_NORMAL%
                        echos          ...Though this may be an invalid skip due to finding %INSERT_TEXT% anywhere in the filename... we're doing a lazy check because this won't happen very often
                        pause
                        goto :Skip
                )

                set target=%file_unquoted%
                set target=%@name[%file_unquoted]%INSERT_TEXT%.%@ext[%file_unquoted]
                if exist "%target%" (
                    set target=%@name[%file_unquoted]-%_PID-%_DATETIME%INSERT_TEXT%.%@ext[%file_unquoted]
                )

                echos %@RandFG[]                    ``
                ren "%file_unquoted%" "%target%" 
                rem /Ns option on `ren` doesn't work right so no way to suppress '1 file renamed' easily
                rem piping to this slows it down: | findstr  /v "file.renamed"
                echo.
                :Skip
            return


:Cleanup
rem >"%inserttrigger%"

:END
