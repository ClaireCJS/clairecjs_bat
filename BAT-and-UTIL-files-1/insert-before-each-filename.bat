@on break cancel
@Echo Off

rem NOTE: Skips BAT files


set                                INSERT_TEXT=%1
call validate-environment-variable INSERT_TEXT
for /h %file in (*) do (gosub processfile "%@UNQUOTE[%file%]")
goto :END

            :processfile [FILE_QUOTED]
                set FILE_UNQUOTED=%@unquote[%file_quoted]
                *cls
                echo.
                echo %ANSI_COLOR_DEBUG%%STAR% Processing file %emphasis%%file_quoted%%deemphasis%...

                iff "%@INSTR[0,%@LEN[%insert_text],%file_unquoted]" == "%@UNQUOTE[%insert_text%]" then
                        echos      %ANSI_COLOR_WARNING%Skipping already-named file %lq%%italics_on%%file_unquoted%%italics_off%%rq%...``%ANSI_COLOR_NORMAL%
                        goto /i :Skip
                endiff
                iff "%@EXT[%file_unquoted%]" == "BAT" then
                        echos      %ANSI_COLOR_WARNING%Skipping %italics_on%BAT%italics_off% file %lq%%italics_on%%file_unquoted%%italics_off%%rq%...``%ANSI_COLOR_NORMAL%
                        goto /i :Skip
                endiff

                set target=%INSERT_TEXT%%file_unquoted%
                iff exist "%target%" then
                    set target=%INSERT_TEXT%%@name[%file_unquoted]-%_PID-%_DATETIME.%@ext[%file_unquoted]
                endiff

                echos %@RandFG[]                    ``
                ren "%@unquote[%file_unquoted%]" "%@unquote[%target%]" 
                rem /Ns option on `ren` doesn't work right so no way to suppress the '1 file renamed' output easily
                rem and piping to this slows it down: | findstr  /v "file.renamed" ... so yea, let that annoying output exist i guess
                echo.
                :Skip
            return


:END
