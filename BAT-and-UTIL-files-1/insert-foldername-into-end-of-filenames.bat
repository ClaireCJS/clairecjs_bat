@on break cancel
@Echo Off
on break goto :breaker

set parent_folder_name=%@FILENAME[%_CWP]
set inserttrigger=__ folder names inserted at end of filenames __
if "%1" eq "SetVarsOnly" (goto :END)

if exist "%inserttrigger%" (
    call warning "Already did this folder. Aborting. (inserttrigger file of %inserttrigger% exists)"
    goto :END
)

echos %ANSI_CURSOR_INVISIBLE%
for /h %file in (*) do (gosub processfile "%@UNQUOTE[%file%]")
echos %ANSI_CURSOR_VISIBLE%
goto :Cleanup

            :processfile [FILE_QUOTED]
                set FILE_UNQUOTED=%@unquote[%file_quoted]
                *cls
                echo %NEWLINE%%ANSI_COLOR_DEBUG%%STAR% Processing file %emphasis%%file_unquoted%%deemphasis%...

                iff "%file_unquoted" eq "%inserttrigger%" .or. %@REGEX[%parent_folder_name,%file_unquoted] eq 1 .or. %@REGEX[%inserttrigger,%file_unquoted] eq 1 then
                        echos %ANSI_COLOR_WARNING%Skipping file '%file_unquoted%'...``
                        goto :Skipe
                endiff

                set target=%@name[%file_unquoted]-%parent_folder_name%.%@ext[%file_unquoted]
                iff exist "%target%" then
                    rem target=%parent_folder_name%-%@name[%file_unquoted]-%_PID-%_DATETIME.%@ext[%file_unquoted]
                    set target=%parent_folder_name%-%@name[%file_unquoted].%@ext[%file_unquoted]
                endiff

                echos %@RandFG[]                    ``
                rem 
                *ren "%file_unquoted%" "%target%" 
                rem echo yra | *move /r /h /E  "%file_unquoted%" "%target%" 
                rem /Ns option on `ren` doesn't work right so no way to suppress '1 file renamed' easily
                rem piping to this slows it down: | findstr  /v "file.renamed"
                rem echo.
                :Skip
            return


:Cleanup
>"%inserttrigger%"

:breaker
:END
echo %ANSI_CURSOR_VISIBLE%

