@Echo Off

set                                INSERT_TEXT=%1
call validate-environment-variable INSERT_TEXT
for /h %file in (*) do (gosub processfile "%@UNQUOTE[%file%]")
goto :END

            :processfile [FILE_QUOTED]
                set FILE_UNQUOTED=%@unquote[%file_quoted]
                *cls
                echo.
                echo %ANSI_COLOR_DEBUG%%STAR% Processing file %emphasis%%file_quoted%%deemphasis%...

                if "%@INSTR[0,%@LEN[%insert_text],%file_unquoted]" eq "%@UNQUOTE[%insert_text%]" (
                        echos      %ANSI_COLOR_WARNING%Skipping file '%file_unquoted%'...``%ANSI_COLOR_NORMAL%
                        goto :Skip
                )

                set target=%INSERT_TEXT%%file_unquoted%
                if exist "%target%" (
                    set target=%INSERT_TEXT%%@name[%file_unquoted]-%_PID-%_DATETIME.%@ext[%file_unquoted]
                )

                echos %@RandFG[]                    ``
                ren "%file_unquoted%" "%target%" 
                rem /Ns option on `ren` doesn't work right so no way to suppress the '1 file renamed' output easily
                rem and piping to this slows it down: | findstr  /v "file.renamed" ... so yea, let that annoying output exist i guess
                echo.
                :Skip
            return


:END
