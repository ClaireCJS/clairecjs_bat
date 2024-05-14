@Echo Off

set parent_folder_name=%@NAME[%_CWP]
set inserttrigger=__ folder names inserted at end of filenames __
if "%1" eq "SetVarsOnly" (goto :END)

if exist "%inserttrigger%" (
    call warning "Already did this folder. Aborting. (inserttrigger file of %inserttrigger% exists)"
    goto :END
)

for /h %file in (*) do (gosub processfile "%@UNQUOTE[%file%]")
goto :Cleanup

            :processfile [FILE_QUOTED]
                set FILE_UNQUOTED=%@unquote[%file_quoted]
                echo %ANSI_COLOR_DEBUG%* Processing file %file_quoted%...

                if "%file_unquoted" eq "%inserttrigger%" .or. %@REGEX[%parent_folder_name,%file_unquoted] eq 1 .or. %@REGEX[%inserttrigger,%file_unquoted] eq 1 (
                        echo %ANSI_COLOR_WARNING%Skipping file '%file_unquoted%'...
                        goto :Skip
                )

                set target=%@name[%file_unquoted]-%parent_folder_name%.%@ext[%file_unquoted]
                if exist "%target%" (
                    set target=%@name[%file_unquoted]-%parent_folder_name%-%_PID-%_DATETIME.%@ext[%file_unquoted]
                )

                echos %@RandFG[]
                ren "%file_unquoted%" "%target%"

                :Skip
            return


:Cleanup
>"%inserttrigger%"

:END
